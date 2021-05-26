import asyncio  # asynchronous operations
import json  # read/write JSON format
import websockets  # sockets made easy and standard
import uuid  # UIDs manipulation

# import LSL's Stream Info and Outlet classes, and sampling rate types
from pylsl import StreamInfo, StreamOutlet, IRREGULAR_RATE


async def on_connect(websocket, _):
    """Listen to messages using WebSockets and then stream them via LSL."""
    try:
        async for message in websocket:
            # Message types (k for key, e for end) and content:
            # Key pressed (M or C) => [timestamp, key, latency, correct/not]
            # End of task => [cnt_good, cnt_bad, perc_good, perc_bad, avg_rt]
            msg = json.loads(message)
            event = msg["msg"]  # event type
            data = msg["value"]  # data read
            unknown = False
            if event == "k":
                # timestamp to send on all streams (UNIX epoch)
                timestamp = int(data[0])
                # send key (1/2)
                key = int(data[1])
                # send latency in milliseconds
                latency = int(data[2])
                # send correct/not (1/0)
                correct = int(data[3])
                # wrap key event values into an array
                key_data = [timestamp, key, latency, correct]
                # send them via LSL
                s_outlet_key.push_sample(key_data)
            elif event == "e":
                # number of correct answers
                cnt_good = int(data[0])
                # number of incorrect answers
                cnt_bad = int(data[1])
                # % of correct answers
                perc_good = int(data[2])
                # % of incorrect answers
                perc_bad = int(data[3])
                # avg reaction time in milliseconds
                avg_rt = int(data[4])
                # wrap end values into an array
                end_data = [cnt_good, cnt_bad, perc_good, perc_bad, avg_rt]
                # send them via LSL
                s_outlet_end.push_sample(end_data)
            else:
                # debug unknown event with keycode sent
                unknown = True
                print(f"Unknown event: {event}")
            if unknown:
                event_name = "Unknown"
            else:
                event_name = "Key" if event == "k" else "End"
            # debugg event with values sent
            print(f"{event_name} event values received => {data}")
    finally:
        print("Connection lost.")


if __name__ == "__main__":
    """Flow of the script."""
    # websockets IP and PORT to listen for incoming messages
    IP = "localhost"
    PORT = 8081

    # generate stream UID (participant unique identifier)
    UID = str(uuid.uuid4())

    # instanciate StreamInfos - more info:
    # https://labstreaminglayer.readthedocs.io/projects/liblsl/ref/streaminfo.html
    s_info_key = StreamInfo(
        name="Key",  # name of the stream
        type="Markers",  # stream type (most usual)
        channel_count=4,  # number of values to stream/send
        nominal_srate=IRREGULAR_RATE,  # sampling rate in Hz or IRREGULAR_RATE
        channel_format="int32",  # datatype: "float32", "int32", "string"...
        # pylsl importable primitive datatypes: 'cf_float32', 'cf_double64',
        # 'cf_string', 'cf_int32', 'cf_int16', 'cf_int8', 'cf_int64',
        # 'cf_undefined'. Source:
        # https://github.com/labstreaminglayer/liblsl-Python/blob/master/pylsl/pylsl.py#L52
        source_id=UID,  # unique identifier
    )
    # add stream metadata (description of fields)
    s_info_key.desc().append_child("Timestamp")
    s_info_key.desc().append_child("Key")
    s_info_key.desc().append_child("Latency")
    s_info_key.desc().append_child("Correct")

    s_info_end = StreamInfo(
        name="End",
        type="Markers",
        channel_count=5,
        nominal_srate=IRREGULAR_RATE,
        channel_format="int32",
        source_id=UID,
    )
    s_info_end.desc().append_child("Correct")
    s_info_end.desc().append_child("NotCorrect")
    s_info_end.desc().append_child("%Correct")
    s_info_end.desc().append_child("%NotCorrect")
    s_info_end.desc().append_child("MeanReactionTime")

    # instanciate StreamOutlets - more info:
    # https://labstreaminglayer.readthedocs.io/projects/liblsl/ref/outlet.html
    s_outlet_key = StreamOutlet(s_info_key)
    s_outlet_end = StreamOutlet(s_info_end)

    lsl_ready_msg = "LSL streams 'Key', 'Latency', 'Correct', and 'End' ready"
    print(f"Listening messages on => {IP}:{PORT}")
    print(f"Participant UID => {UID}")
    print(f"=> {lsl_ready_msg}")

    # Make sure IP and PORT match with Labvanced's study settings
    listener = websockets.serve(on_connect, IP, PORT)
    asyncio.get_event_loop().run_until_complete(listener)
    asyncio.get_event_loop().run_forever()
