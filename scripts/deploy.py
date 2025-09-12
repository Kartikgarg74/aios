import subprocess
import sys

def run_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        sys.exit(1)

def deploy_all():
    print("Building and deploying all services...")
    run_command("docker compose build")
    run_command("docker compose up -d")
    print("All services deployed.")

def stop_all():
    print("Stopping all services...")
    run_command("docker compose down")
    print("All services stopped.")

def main():
    if len(sys.argv) < 2:
        print("Usage: python deploy.py [deploy|stop]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "deploy":
        deploy_all()
    elif command == "stop":
        stop_all()
    else:
        print(f"Unknown command: {command}")
        print("Usage: python deploy.py [deploy|stop]")
        sys.exit(1)

if __name__ == "__main__":
    main()