import asyncio  # asynchronous operations
import json  # read/write JSON format
import websockets  # sockets made easy and standard
import uuid  # UIDs manipulation

# import LSL's Stream Info and Outlet classes, data and sampling rate types
from pylsl import StreamInfo, StreamOutlet, IRREGULAR_RATE


async def on_connect(websocket, path):
    try:
        async for message in websocket:
            # Message types and content:
            # Key pressed (M or C) => [timestamp, key, latency, correct/not]
            # End of task => [cnt_good, cnt_bad, perc_good, perc_bad, avg_RT]
            msg = json.loads(message)
            event = msg["msg"]  # event type
            if event == "key":
                # timestamp to send on all streams
                timestamp = msg["value"][0]
                # send key
                key = str(msg["value"][1])
                s_outlet_key.push([timestamp, key])
                # send latency
                latency = float(msg["value"][2])
                s_outlet_lat.push([timestamp, latency])
                # send correct/not (1/0)
                correct = int(msg["value"][3])
                s_outlet_cor.push([timestamp, correct])
                # debugger
                print(f"Values received and sent => {lsl_ready_msg}")
            elif event == "end":
                # send end values
                end_values = [float(v) for v in msg["value"]]
                s_outlet_end.push(end_values)
            else:
                print(f"Unknown event: {event}")

    finally:
        print("Connection lost.")


if __name__ == "__main__":
    """Flow of the script."""
    # websockets IP and PORT to listen for incoming messages
    IP = "localhost"
    PORT = 8081
    print(f"Listening messages on => {IP}:{PORT}")

    # generate stream UID (participant unique identifier)
    UID = str(uuid.uuid4())
    print(f"Participant UID => {UID}")

    # instanciate StreamInfos - more info:
    # https://labstreaminglayer.readthedocs.io/projects/liblsl/ref/streaminfo.html
    s_info_key = StreamInfo(
        name="Key",  # name of the stream
        type="Markers",  # stream type (most usual)
        channel_count=2,  # number of values to stream/send
        nominal_srate=IRREGULAR_RATE,  # sampling rate in Hz or IRREGULAR_RATE
        channel_format="string",  # datatype: "float32", "int32", "string"...
        # pylsl importable primitive datatypes: 'cf_float32', 'cf_double64',
        # 'cf_string', 'cf_int32', 'cf_int16', 'cf_int8', 'cf_int64',
        # 'cf_undefined'. Source:
        # https://github.com/labstreaminglayer/liblsl-Python/blob/master/pylsl/pylsl.py#L52
        source_id=UID,  # unique identifier
    )
    s_info_lat = StreamInfo(
        name="Latency",
        type="Markers",
        channel_count=2,
        nominal_srate=IRREGULAR_RATE,
        channel_format="float32",
        source_id=UID,
    )
    s_info_cor = StreamInfo(
        name="Correct",
        type="Markers",
        channel_count=2,
        nominal_srate=IRREGULAR_RATE,
        channel_format="int32",
        source_id=UID,
    )
    s_info_end = StreamInfo(
        name="End",
        type="Markers",
        channel_count=5,
        nominal_srate=IRREGULAR_RATE,
        channel_format="float32",
        source_id=UID,
    )

    # instanciate StreamOutlets - more info:
    # https://labstreaminglayer.readthedocs.io/projects/liblsl/ref/outlet.html
    s_outlet_key = StreamOutlet(s_info_key)
    s_outlet_lat = StreamOutlet(s_info_lat)
    s_outlet_cor = StreamOutlet(s_info_cor)
    s_outlet_end = StreamOutlet(s_info_end)

    lsl_ready_msg = "LSL streams 'Key', 'Latency', 'Correct', and 'End' ready"
    print(f"=> {lsl_ready_msg}")

    # Make sure IP and PORT match with Labvanced's study settings
    listener = websockets.serve(on_connect, IP, PORT)
    asyncio.get_event_loop().run_until_complete(listener)
    asyncio.get_event_loop().run_forever()
