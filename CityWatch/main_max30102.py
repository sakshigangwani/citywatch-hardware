from heartrate_monitor import HeartRateMonitor
import time
import argparse

def read_heart_rate():
    parser = argparse.ArgumentParser(description="Read and print data from MAX30102")
    parser.add_argument("-r", "--raw", action="store_true",
                        help="print raw data instead of calculation result")
    parser.add_argument("-t", "--time", type=int, default=10,
                        help="duration in seconds to read from sensor, default 30")
    parser.add_argument("--firebase", action="store_true",
                        help="Enable Firestore data storage")
    parser.add_argument("--user-address", action="store_true",
                        help="Get address of user based on IP address")
    args = parser.parse_args()

    print('sensor starting...')
    hrm = HeartRateMonitor(print_raw=args.raw, print_result=(not args.raw))
    hrm.start_sensor()

    try:
        time.sleep(args.time)
    except KeyboardInterrupt:
        print('keyboard interrupt detected, exiting...')

    heart_rate = hrm.get_heart_rate()
    spo2 = hrm.get_spo2()

    hrm.stop_sensor()
    print('sensor stopped!')

    return heart_rate, spo2

if __name__ == "__main__":
    heart_rate = read_heart_rate()
    print(f"Heart Rate: {heart_rate}")
