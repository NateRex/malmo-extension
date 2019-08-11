# ------------------------------------------------------------------------------------------------
# Copyright (c) 2016 Microsoft Corporation
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
# associated documentation files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge, publish, distribute,
# sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT
# NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# ------------------------------------------------------------------------------------------------

from __future__ import print_function

import malmoext.MalmoPython as MalmoPython
from malmoext.Agent import *
from malmoext.MissionBuilder import *
import os
import sys
import errno
import time

# GLOBALS - stored as a mission is created and loaded
CLIENT_POOL = None
MISSION = None
AGENTS = []


# ORIGINAL MALMO FUNCTIONS ======================================================================================

def __fix_print__():
    # We want to flush the print output immediately, so that we can view test output as it happens.
    # The way to do this changed completely between Python 2 and 3, with the result that setting this
    # in a cross-compatible way requires a few lines of ugly code.
    # Rather than include this mess in every single sample, it's nice to wrap it into a handy
    # function - hence this.
    if sys.version_info[0] == 2:
        sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)  # flush print output immediately
    else:
        import functools
        # Have to assign to builtins or the change won't make it outside of this module's scope
        import builtins
        builtins.print = functools.partial(print, flush=True)

def __parse_command_line__(agent_host, argv=None):
    if argv is None:
       argv = sys.argv
    # Add standard options required by test suite:
    agent_host.addOptionalStringArgument( "recording_dir,r", "Path to location for saving mission recordings", "" )
    agent_host.addOptionalFlag( "record_video,v", "Record video stream" )
    # Attempt to parse:
    try:
        agent_host.parse(argv)
    except RuntimeError as e:
        print('ERROR:',e)
        print(agent_host.getUsage())
        exit(1)
    if agent_host.receivedArgument("help"):
        print(agent_host.getUsage())
        exit(0)


def __get_video_xml__(agent_host):
    return '<VideoProducer><Width>860</Width><Height>480</Height></VideoProducer>' if agent_host.receivedArgument("record_video") else ''

def __get_default_recording_object__(agent_host, filename):
    # Convenience method for setting up a recording object - assuming the recording_dir and record_video
    # flags were passed in as command line arguments (see parse_command_line above).
    # (If no recording destination was passed in, we assume no recording is required.)
    my_mission_record = MalmoPython.MissionRecordSpec()
    recordingsDirectory = __get_recordings_directory__(agent_host)
    if recordingsDirectory:
        my_mission_record.setDestination(recordingsDirectory + "//" + filename + ".tgz")
        my_mission_record.recordRewards()
        my_mission_record.recordObservations()
        my_mission_record.recordCommands()
        if agent_host.receivedArgument("record_video"):
            my_mission_record.recordMP4(24,2000000)
    return my_mission_record

def __get_recordings_directory__(agent_host):
    # Check the dir passed in:
    recordingsDirectory = agent_host.getStringArgument('recording_dir')
    if recordingsDirectory:
        # If we're running as an integration test, we want to send all our recordings
        # to the central test location specified in the environment variable MALMO_TEST_RECORDINGS_PATH:
        if agent_host.receivedArgument("test"):
            try:
                test_path = os.environ['MALMO_TEST_RECORDINGS_PATH']
                if test_path:
                    recordingsDirectory = os.path.join(test_path, recordingsDirectory)
            except:
                pass
        # Now attempt to create the folder we want to write to:
        try:
            os.makedirs(recordingsDirectory)
        except OSError as exception:
            if exception.errno != errno.EEXIST: # ignore error if already existed
                raise
    return recordingsDirectory

def __safeMissionStart__(agent_host, mission, client_pool, recording, role, experimentId):
    used_attempts = 0
    max_attempts = 5
    print("Calling startMission for role", role)
    while True:
        try:
            agent_host.startMission(mission, client_pool, recording, role, experimentId)
            break
        except MalmoPython.MissionException as e:
            errorCode = e.details.errorCode
            if errorCode == MalmoPython.MissionErrorCode.MISSION_SERVER_WARMING_UP:
                print("Server not quite ready yet - waiting...")
                time.sleep(2)
            elif errorCode == MalmoPython.MissionErrorCode.MISSION_INSUFFICIENT_CLIENTS_AVAILABLE:
                print("Not enough available Minecraft instances running.")
                used_attempts += 1
                if used_attempts < max_attempts:
                    print("Will wait in case they are starting up.", max_attempts - used_attempts, "attempts left.")
                    time.sleep(2)
            elif errorCode == MalmoPython.MissionErrorCode.MISSION_SERVER_NOT_FOUND:
                print("Server not found - has the mission with role 0 been started yet?")
                used_attempts += 1
                if used_attempts < max_attempts:
                    print("Will wait and retry.", max_attempts - used_attempts, "attempts left.")
                    time.sleep(2)
            else:
                print("Other error:", e.message)
                print("Waiting will not help here - bailing immediately.")
                exit(1)
        if used_attempts == max_attempts:
            print("All chances used up - bailing now.")
            exit(1)
    print("startMission called okay.")

def __safeWaitForStart__(agent_hosts):
    print("Waiting for the mission to start", end=' ')
    start_flags = [False for a in agent_hosts]
    start_time = time.time()
    time_out = 120  # Allow two minutes for mission to start.
    while not all(start_flags) and time.time() - start_time < time_out:
        states = [a.peekWorldState() for a in agent_hosts]
        start_flags = [w.has_mission_begun for w in states]
        errors = [e for w in states for e in w.errors]
        if len(errors) > 0:
            print("Errors waiting for mission start:")
            for e in errors:
                print(e.text)
            print("Bailing now.")
            exit(1)
        time.sleep(0.1)
        print(".", end=' ')
    print()
    if time.time() - start_time >= time_out:
        print("Timed out waiting for mission to begin. Bailing.")
        exit(1)
    print("Mission has started.")




# MALMO-EXTENSION ADDED FUNCTIONS ====================================================================================


def initializeMalmo(numberOfAgents = 1):
    '''
    Initialize Microsoft's Malmo Platform by connecting to running clients.
    '''
    global CLIENT_POOL
    MalmoPython.setLogging("", MalmoPython.LoggingSeverityLevel.LOG_OFF)
    CLIENT_POOL = MalmoPython.ClientPool()
    for i in range(10000, 10000 + numberOfAgents):
        CLIENT_POOL.add( MalmoPython.ClientInfo('127.0.0.1',10000) )
        CLIENT_POOL.add( MalmoPython.ClientInfo('127.0.0.1',10001) )

def loadMission(builder):
    '''
    Load a mission to run by supplying a MissionBuilder object.
    '''
    global MISSION, AGENTS

    # Load the environment XML
    MISSION = MalmoPython.MissionSpec(builder.finish(), True)
    
    # Load the agents
    allAgents = list(Agent.allAgents.values())
    __parse_command_line__(allAgents[0].getMalmoAgent())
    AGENTS = allAgents

def startMission():
    '''
    Start the mission previously loaded.
    '''
    i = 0
    agent_hosts = list(map(lambda x: x.getMalmoAgent(), AGENTS))
    for host in agent_hosts:
        __safeMissionStart__(host, MISSION, CLIENT_POOL, __get_default_recording_object__(agent_hosts[0], "agent_{}_viewpoint_continuous".format(i + 1)), i, '')
        i += 1
    __safeWaitForStart__(agent_hosts)

    # Make sure that atleast one observation has come through before releasing control
    while AGENTS[0].toJSON() == None:
        continue

def isMissionActive():
    '''
    Returns true if the mission is still active/running, false otherwise.
    '''
    for agent in list(Agent.allAgents.values()):
        if agent.isMissionActive():
            return True
    return False
