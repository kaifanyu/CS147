import RPi.GPIO as GPIO
import time
import requests
import sys
import select
import subprocess

class SoilMoistureSystem:
    def __init__(self, soil_pin, motor_pin, speaker_pin, cloud_server_url):
        self.timer = 0
        self.SOIL_PIN = soil_pin
        self.MOTOR_PIN = motor_pin
        self.SPEAKER_PIN = speaker_pin
        self.CLOUD_SERVER_URL = cloud_server_url

        self.motor_status = False
        self.speaker_status = False
        self.water_status = False

        self.script_path = "pump.sh"

        # GPIO setup
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.MOTOR_PIN, GPIO.OUT)
        GPIO.setup(self.SPEAKER_PIN, GPIO.OUT)
        GPIO.setup(self.SOIL_PIN, GPIO.IN)

        # PWM setup for motor
        self.motor_pwm = GPIO.PWM(self.MOTOR_PIN, 50)  # Set frequency to 50Hz
        self.motor_pwm.start(0)  # Start PWM with 0 duty cycle

        # PWM setup
        self.speaker_pwm = GPIO.PWM(self.SPEAKER_PIN, 440)  # Start with 440Hz
        self.speaker_pwm.start(0)

        # Define melody (frequency in Hz and duration in seconds)
        self.melody = [
            (440, 0.5),  # A4
            (494, 0.5),  # B4
            (523, 0.5),  # C5
            (440, 0.5)   # A4
        ]

        self.control_water()

    def read_soil(self):
        soil_level = GPIO.input(self.SOIL_PIN)
        if soil_level:
            self.water_status = True
            print("Dry Soil")
        else:
            self.water_status = False   #change water status to water plant
            print("Wet Soil")
        return soil_level

    def send_soil(self, soil_value):
        try:
            response = requests.post(f"{self.CLOUD_SERVER_URL}/data", json={"soil_moisture": soil_value})
            if response.status_code == 200:
                print("Status sent to cloud successfully.")
            else:
                print(f"Failed to send status to cloud: {response.status_code}")
        except Exception as e:
            print(f"Error sending status to cloud: {e}")

    def process_command(self):
        try:
            response = requests.get(f"{self.CLOUD_SERVER_URL}/command")
            if response.status_code == 200:
                command = response.json().get('command', '').lower()
                print("Command: ", command)

                if command == 'move motor':
                    self.motor_status = True
                elif command == 'stop motor':
                    self.motor_status = False
                elif command == 'play sound':
                    self.speaker_status = True
                elif command == 'stop sound':
                    self.speaker_status = False
                elif command == 'start water':
                    self.water_status = True
                elif command == 'stop water':
                    self.water_status = False   
                else:
                    print("Invalid command received.")
            else:
                print(f"Failed to fetch command: {response.status_code}")
        except Exception as e:
            print(f"Error fetching command: {e}")

    def control_water(self):
        """
        Run a shell script to control USB hub ports.
        :param script_path: Path to the shell script.
        :param action: 'on' or 'off' to pass as an argument to the shell script.
        """
        if self.water_status:
            action = "on"
            try:
                # Run the shell script with the action as an argument
                result = subprocess.run(
                    ["bash", self.script_path, action],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    print(f"Shell script executed successfully with action: {action}")
                    print(result.stdout)
                else:
                    print(f"Error executing shell script: {result.stderr}")
            except Exception as e:
                print(f"An error occurred: {e}")
        else:
            action = "off"
            try:
                # Run the shell script with the action as an argument
                result = subprocess.run(
                    ["bash", self.script_path, action],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    print(f"Shell script executed successfully with action: {action}")
                    print(result.stdout)
                else:
                    print(f"Error executing shell script: {result.stderr}")
            except Exception as e:
                print(f"An error occurred: {e}")
            print("Water is stopped")



    def control_motor(self):
        if self.motor_status:
            print("Activating motor...")
            # Move motor from 0 to 180 degrees and back to 0
            for angle in range(0, 181, 10):  # Increment by 10 degrees
                duty_cycle = self.angle_to_duty_cycle(angle)
                self.motor_pwm.ChangeDutyCycle(duty_cycle)
                time.sleep(0.05)  # Delay for smooth motion

            for angle in range(180, -1, -10):  # Decrement by 10 degrees
                duty_cycle = self.angle_to_duty_cycle(angle)
                self.motor_pwm.ChangeDutyCycle(duty_cycle)
                time.sleep(0.05)
        else:
            print("Motor is stopped.")
            self.motor_pwm.ChangeDutyCycle(0)  # Stop the motor

    def control_speaker(self):
        if self.speaker_status:
            print("Playing melody...")
            for frequency, duration in self.melody:
                self.speaker_pwm.ChangeFrequency(frequency)
                self.speaker_pwm.ChangeDutyCycle(50)  # 50% duty cycle for sound
                time.sleep(duration)
            self.speaker_pwm.ChangeDutyCycle(0)  # Stop sound after melody
        else:
            print("Speaker is stopped.")
            self.speaker_pwm.ChangeDutyCycle(0)  # Ensure speaker is off

    def angle_to_duty_cycle(self, angle):
        # Convert angle (0 to 180) to duty cycle (2% to 12% for typical servos)
        return 2 + (angle / 180) * 10

    def run(self):
        try:
            print("Press 'q' to quit.")
            while True:
                
                # increment timer, only send soil data once every mintue
                self.timer += 1
                if self.timer % 10 == 0:
                    # Read and send soil value
                    soil_value = self.read_soil()
                    self.send_soil(soil_value)
                    self.timer = 0
                    print(f"Soil value: {soil_value}")

                # Process commands
                self.process_command()

                # activate motor / speaker based on status
                self.control_motor()
                self.control_speaker()
                self.control_water()

                # Display statuses
                print(f"Speaker: {self.speaker_status}, Motor: {self.motor_status}, Water: {self.water_status}")
                print("---------------------------------------------")
                
                time.sleep(1)

        except KeyboardInterrupt:
            print("\nProgram interrupted by user.")
        finally:
            self.motor_pwm.stop()  # Stop PWM
            GPIO.cleanup()
            print("GPIO cleanup done. Goodbye!")

if __name__ == "__main__":
    # Initialize system with appropriate pins and server URL
    system = SoilMoistureSystem(
        soil_pin=17,
        motor_pin=18,
        speaker_pin=26,
        cloud_server_url="http://44.201.87.23:5000"
    )

    # Run the system
    system.run()
