#!/usr/bin/env python3
"""
Vast.ai Auto-Launcher for FRA Scaling Experiment
=================================================

Fully automated deployment:
1. Find cheapest GPU instances
2. Deploy experiment code
3. Run experiment in parallel
4. Monitor progress
5. Collect results
6. Destroy instances

Usage:
    # Full auto
    python vast_launcher.py --deploy

    # Monitor running experiment
    python vast_launcher.py --status

    # Download results
    python vast_launcher.py --download

    # Cleanup
    python vast_launcher.py --destroy

Requirements:
    pip install vastai paramiko
    vastai set api-key YOUR_KEY

Author: Ilya Selyutin
"""

import os
import sys
import json
import subprocess
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import tarfile
import tempfile


class VastAILauncher:
    """Automated vast.ai experiment launcher."""

    # Proven working image
    DOCKER_IMAGE = "pytorch/pytorch:2.4.0-cuda12.1-cudnn9-runtime"

    # State file
    STATE_FILE = Path(__file__).parent / "vast_state.json"

    def __init__(self, budget_limit: float = 25.0):
        self.budget_limit = budget_limit
        self.state = self._load_state()
        self.experiment_dir = Path(__file__).parent

    def _load_state(self) -> Dict:
        """Load launcher state."""
        if self.STATE_FILE.exists():
            with open(self.STATE_FILE) as f:
                return json.load(f)
        return {"instances": [], "started_at": None, "total_spent": 0}

    def _save_state(self):
        """Save launcher state."""
        with open(self.STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _run_cmd(self, cmd: str, capture: bool = True) -> str:
        """Run shell command."""
        result = subprocess.run(cmd, shell=True, capture_output=capture, text=True)
        if capture:
            return result.stdout.strip()
        return ""

    def _check_vastai(self) -> bool:
        """Check vastai CLI is configured."""
        try:
            result = self._run_cmd("vastai show instances --raw")
            return True
        except:
            print("❌ vastai CLI not configured")
            print("   Install: pip install vastai")
            print("   Configure: vastai set api-key YOUR_KEY")
            return False

    def search_gpus(self, gpu_type: str = "RTX_3090", max_price: float = 0.30) -> List[Dict]:
        """Search for available GPU instances."""
        query = f'gpu_name={gpu_type} disk_space>=50 dph<={max_price} rentable=true inet_down>=100'
        cmd = f'vastai search offers "{query}" -o dph --raw'
        result = self._run_cmd(cmd)

        if not result:
            return []

        try:
            return json.loads(result)
        except:
            return []

    def create_instance(self, offer_id: int, disk: int = 50) -> Optional[int]:
        """Create a vast.ai instance."""
        cmd = f'vastai create instance {offer_id} --image {self.DOCKER_IMAGE} --disk {disk} --raw'
        result = self._run_cmd(cmd)

        try:
            data = json.loads(result)
            return data.get('new_contract')
        except:
            print(f"Failed to create instance: {result}")
            return None

    def wait_for_instance(self, instance_id: int, timeout: int = 300) -> Optional[Dict]:
        """Wait for instance to be running."""
        start = time.time()
        while time.time() - start < timeout:
            info = self.get_instance_info(instance_id)
            if info and info.get('actual_status') == 'running':
                return info
            print(f"  Waiting for instance {instance_id}... ({int(time.time()-start)}s)")
            time.sleep(15)
        return None

    def get_instance_info(self, instance_id: int) -> Optional[Dict]:
        """Get instance info."""
        cmd = f'vastai show instance {instance_id} --raw'
        result = self._run_cmd(cmd)
        try:
            return json.loads(result)
        except:
            return None

    def ssh_cmd(self, info: Dict, command: str, capture: bool = True) -> str:
        """Run SSH command on instance."""
        host = info.get('ssh_host', info.get('public_ipaddr'))
        port = info.get('ssh_port', 22)

        cmd = f'ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 -p {port} root@{host} "{command}"'
        return self._run_cmd(cmd, capture=capture)

    def scp_upload(self, info: Dict, local_path: str, remote_path: str = "/workspace/"):
        """Upload file to instance."""
        host = info.get('ssh_host', info.get('public_ipaddr'))
        port = info.get('ssh_port', 22)

        cmd = f'scp -o StrictHostKeyChecking=no -P {port} -r "{local_path}" root@{host}:{remote_path}'
        self._run_cmd(cmd, capture=False)

    def scp_download(self, info: Dict, remote_path: str, local_path: str):
        """Download file from instance."""
        host = info.get('ssh_host', info.get('public_ipaddr'))
        port = info.get('ssh_port', 22)

        cmd = f'scp -o StrictHostKeyChecking=no -P {port} -r root@{host}:{remote_path} "{local_path}"'
        self._run_cmd(cmd, capture=False)

    def destroy_instance(self, instance_id: int):
        """Destroy instance."""
        self._run_cmd(f'vastai destroy instance {instance_id}')

    def package_experiment(self) -> str:
        """Package experiment code into tarball."""
        tarball_path = self.experiment_dir / "experiment_package.tar.gz"

        with tarfile.open(tarball_path, "w:gz") as tar:
            # Add all Python files
            for py_file in self.experiment_dir.glob("**/*.py"):
                arcname = py_file.relative_to(self.experiment_dir)
                tar.add(py_file, arcname=arcname)

            # Add config
            config_file = self.experiment_dir / "config.yaml"
            if config_file.exists():
                tar.add(config_file, arcname="config.yaml")

            # Add requirements
            req_file = self.experiment_dir / "requirements.txt"
            if req_file.exists():
                tar.add(req_file, arcname="requirements.txt")

        return str(tarball_path)

    def deploy(self, n_instances: int = 3, gpu_type: str = "RTX_3090", max_price: float = 0.30):
        """
        Deploy experiment to vast.ai.

        Strategy: 3 instances, one per problem (TSP, SAT, MaxCut)
        """
        if not self._check_vastai():
            return

        print("\n" + "="*60)
        print("🚀 FRA SCALING EXPERIMENT - VAST.AI DEPLOYMENT")
        print("="*60)

        # Check budget
        print(f"\n💰 Budget limit: ${self.budget_limit:.2f}")
        print(f"   Already spent: ${self.state.get('total_spent', 0):.2f}")

        # Search for GPUs
        print(f"\n🔍 Searching for {n_instances}x {gpu_type} @ max ${max_price}/hr...")
        offers = self.search_gpus(gpu_type, max_price)

        if len(offers) < n_instances:
            # Try alternative GPUs
            print(f"   Only {len(offers)} found, trying RTX 4090...")
            offers = self.search_gpus("RTX_4090", max_price + 0.20)

        if len(offers) < n_instances:
            print(f"❌ Not enough instances available")
            return

        print(f"   Found {len(offers)} offers")

        # Estimate cost
        total_price = sum(o.get('dph_total', 0) for o in offers[:n_instances])
        estimated_runtime = 2.0  # hours
        estimated_cost = total_price * estimated_runtime

        print(f"\n📊 Cost estimate:")
        print(f"   Per hour: ${total_price:.2f}")
        print(f"   Est. runtime: {estimated_runtime}h")
        print(f"   Est. total: ${estimated_cost:.2f}")

        if estimated_cost > self.budget_limit:
            print(f"❌ Estimated cost exceeds budget!")
            return

        # Package experiment
        print(f"\n📦 Packaging experiment...")
        tarball = self.package_experiment()
        print(f"   Created: {tarball}")

        # Create instances
        print(f"\n🖥️ Creating {n_instances} instances...")
        problems = ["tsp", "sat", "maxcut"]

        for i in range(n_instances):
            offer = offers[i]
            offer_id = offer['id']
            gpu_name = offer.get('gpu_name', 'Unknown')
            price = offer.get('dph_total', 0)

            print(f"\n   [{i+1}/{n_instances}] {gpu_name} @ ${price:.3f}/hr")

            instance_id = self.create_instance(offer_id)
            if not instance_id:
                print(f"   ❌ Failed to create instance")
                continue

            print(f"   Instance ID: {instance_id}")

            self.state["instances"].append({
                "id": instance_id,
                "problem": problems[i],
                "gpu": gpu_name,
                "price": price,
                "created_at": datetime.now().isoformat(),
                "status": "creating"
            })
            self._save_state()

        # Wait for instances
        print(f"\n⏳ Waiting for instances to start...")
        for inst in self.state["instances"]:
            info = self.wait_for_instance(inst["id"])
            if info:
                inst["status"] = "running"
                inst["ssh_host"] = info.get('ssh_host')
                inst["ssh_port"] = info.get('ssh_port')
                print(f"   ✅ Instance {inst['id']} ({inst['problem']}): running")
            else:
                inst["status"] = "failed"
                print(f"   ❌ Instance {inst['id']}: failed to start")

        self._save_state()

        # Deploy code to running instances
        print(f"\n📤 Deploying experiment code...")
        for inst in self.state["instances"]:
            if inst["status"] != "running":
                continue

            info = {"ssh_host": inst["ssh_host"], "ssh_port": inst["ssh_port"]}

            # Wait for SSH
            time.sleep(10)

            # Create workspace
            self.ssh_cmd(info, "mkdir -p /workspace/experiment")

            # Upload tarball
            self.scp_upload(info, tarball, "/workspace/")

            # Extract
            self.ssh_cmd(info, "cd /workspace && tar -xzf experiment_package.tar.gz -C experiment/")

            # Install dependencies
            print(f"   Installing dependencies on {inst['id']}...")
            self.ssh_cmd(info, "pip install -q pyyaml scipy scikit-learn torch tqdm python-sat")

            inst["status"] = "deployed"
            print(f"   ✅ Deployed to {inst['id']} ({inst['problem']})")

        self._save_state()

        # Start experiments
        print(f"\n🎯 Starting experiments...")
        self.state["started_at"] = datetime.now().isoformat()

        for inst in self.state["instances"]:
            if inst["status"] != "deployed":
                continue

            info = {"ssh_host": inst["ssh_host"], "ssh_port": inst["ssh_port"]}
            problem = inst["problem"]

            # Run experiment in background
            cmd = f"""cd /workspace/experiment && nohup python run_experiment.py \\
                --local --instances 100 --problem {problem} \\
                > /workspace/experiment_{problem}.log 2>&1 &"""

            self.ssh_cmd(info, cmd)
            inst["status"] = "running_experiment"
            print(f"   ✅ Started experiment on {inst['id']} ({problem})")

        self._save_state()

        print(f"\n" + "="*60)
        print("✅ DEPLOYMENT COMPLETE!")
        print("="*60)
        print(f"""
Next steps:
1. Monitor: python vast_launcher.py --status
2. Wait for completion (est. 1-2 hours)
3. Download: python vast_launcher.py --download
4. Cleanup: python vast_launcher.py --destroy
""")

    def status(self):
        """Check experiment status."""
        if not self.state.get("instances"):
            print("No active instances")
            return

        print("\n" + "="*60)
        print("📊 EXPERIMENT STATUS")
        print("="*60)

        total_cost = 0
        started_at = self.state.get("started_at")
        if started_at:
            runtime = (datetime.now() - datetime.fromisoformat(started_at)).total_seconds() / 3600
            print(f"\nRuntime: {runtime:.2f} hours")

        for inst in self.state["instances"]:
            print(f"\n--- Instance {inst['id']} ({inst['problem']}) ---")
            print(f"    GPU: {inst['gpu']}")
            print(f"    Price: ${inst['price']:.3f}/hr")

            if inst.get("ssh_host"):
                info = {"ssh_host": inst["ssh_host"], "ssh_port": inst["ssh_port"]}

                # Check if experiment is done
                log_check = self.ssh_cmd(info, f"tail -3 /workspace/experiment_{inst['problem']}.log 2>/dev/null")
                print(f"    Latest log: {log_check[:80] if log_check else 'N/A'}...")

                # Check GPU usage
                gpu_usage = self.ssh_cmd(info, "nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader 2>/dev/null")
                print(f"    GPU usage: {gpu_usage if gpu_usage else 'N/A'}")

                # Check if results exist
                results_check = self.ssh_cmd(info, "ls -la /workspace/experiment/results/ 2>/dev/null")
                if "experiment_results.json" in results_check:
                    print(f"    Status: ✅ COMPLETED")
                    inst["status"] = "completed"
                else:
                    print(f"    Status: 🔄 Running")

            if started_at:
                cost = inst['price'] * runtime
                total_cost += cost
                print(f"    Cost so far: ${cost:.2f}")

        print(f"\n💰 Total cost: ${total_cost:.2f} / ${self.budget_limit:.2f}")
        self._save_state()

    def download(self):
        """Download results from all instances."""
        if not self.state.get("instances"):
            print("No instances to download from")
            return

        results_dir = self.experiment_dir / "results"
        results_dir.mkdir(exist_ok=True)

        print("\n📥 Downloading results...")

        for inst in self.state["instances"]:
            if not inst.get("ssh_host"):
                continue

            info = {"ssh_host": inst["ssh_host"], "ssh_port": inst["ssh_port"]}
            problem = inst["problem"]

            local_dir = results_dir / problem
            local_dir.mkdir(exist_ok=True)

            # Download results
            self.scp_download(info, "/workspace/experiment/results/*", str(local_dir))

            # Download logs
            self.scp_download(info, f"/workspace/experiment_{problem}.log", str(local_dir))

            print(f"   ✅ Downloaded {problem} results to {local_dir}")

        print(f"\n✅ All results downloaded to {results_dir}")

    def destroy(self):
        """Destroy all instances."""
        if not self.state.get("instances"):
            print("No instances to destroy")
            return

        print("\n🗑️ Destroying instances...")

        for inst in self.state["instances"]:
            instance_id = inst["id"]
            self.destroy_instance(instance_id)
            print(f"   Destroyed: {instance_id}")

        # Calculate final cost
        started_at = self.state.get("started_at")
        if started_at:
            runtime = (datetime.now() - datetime.fromisoformat(started_at)).total_seconds() / 3600
            total_cost = sum(inst['price'] * runtime for inst in self.state["instances"])
            print(f"\n💰 Total cost: ${total_cost:.2f}")

        # Clear state
        self.state = {"instances": [], "started_at": None, "total_spent": 0}
        self._save_state()

        print("✅ All instances destroyed")


def main():
    parser = argparse.ArgumentParser(description="Vast.ai FRA Experiment Launcher")
    parser.add_argument("--deploy", action="store_true", help="Deploy experiment")
    parser.add_argument("--status", action="store_true", help="Check status")
    parser.add_argument("--download", action="store_true", help="Download results")
    parser.add_argument("--destroy", action="store_true", help="Destroy instances")
    parser.add_argument("--budget", type=float, default=25.0, help="Budget limit in USD")
    parser.add_argument("--instances", type=int, default=3, help="Number of instances")
    parser.add_argument("--gpu", type=str, default="RTX_3090", help="GPU type")
    parser.add_argument("--max-price", type=float, default=0.30, help="Max price per hour")

    args = parser.parse_args()

    launcher = VastAILauncher(budget_limit=args.budget)

    if args.deploy:
        launcher.deploy(n_instances=args.instances, gpu_type=args.gpu, max_price=args.max_price)
    elif args.status:
        launcher.status()
    elif args.download:
        launcher.download()
    elif args.destroy:
        launcher.destroy()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
