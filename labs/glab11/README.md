# Graduate Lab 11: Run a Hypervisor

Note: This is the first of five graduate labs.

# Lab: Local Hypervisor and Ubuntu VM Setup

## Objective
Set up a local virtualization environment and create your first Ubuntu virtual machine. This lab introduces you to hypervisor technology—a fundamental building block for cloud computing and data science infrastructure work.

**Estimated time:** 30-60 minutes

---

## Part 1: Setup

### Step 1: Choose and Install a Hypervisor

Select one of these free hypervisors based on your operating system:

**Recommended Options:**
- **VirtualBox** (Oracle) - Works on Windows, macOS, Linux
  - Download: https://www.virtualbox.org/wiki/Downloads
  - Most beginner-friendly, cross-platform
  
- **VMware Workstation Player** (Windows/Linux) or **VMware Fusion Player** (macOS)
  - Download: https://www.vmware.com/products/desktop-hypervisor.html
  - Professional-grade, free for personal use

- **QEMU + UTM** (macOS, especially Apple Silicon)
  - Download: https://mac.getutm.app/
  - Best option for M1/M2/M3 Macs

- **Hyper-V** (Windows Pro/Enterprise only)
  - Built into Windows, enable through Windows Features
  - Requires Windows Pro or higher

Install your chosen hypervisor following the vendor's instructions.

### Step 2: Download Ubuntu 24.04 LTS

Download the Ubuntu 24.04 LTS Desktop ISO image:
- **Direct link:** https://ubuntu.com/download/desktop
- Select either the standard Desktop version (approximately 5-6 GB), or the [server version](https://ubuntu.com/download/server).

### Step 3: Create Your Virtual Machine

Using your hypervisor:
1. Create a new virtual machine
2. Point it to the Ubuntu ISO you downloaded
3. Allocate reasonable resources (suggestion: 2+ CPU cores, 4+ GB RAM, 10+ GB disk)
4. Start the VM and follow Ubuntu's installation prompts
5. Create a default user and password when prompted

---

## Part 2: Exploration & Questions

Once your VM is running, explore its capabilities and answer the following questions. Document your findings and submit your responses.

### Question 1: Internet Connectivity
Can your VM connect to the internet? Test this and describe how you verified connectivity. What networking mode is your VM using (NAT, bridged, host-only, etc.)?

### Question 2: SSH Access
Can you SSH into your VM from your host machine? If yes, describe the steps you took. If no, what would be required to enable this?

### Question 3: Web Resources
From inside the VM, can you use `curl` or `wget` to retrieve web resources? Test this with a simple command and report your results.

### Question 4: File System Integration
Can you map or mount your host machine's hard drive into the VM? Is the VM completely isolated, or can it access host files? Describe what you discovered.

### Question 5: Challenges
What difficulties or challenges did you encounter during this process? What's a key takeaway or two that you learned from troubleshooting them?

---

## Submission

Submit a document (PDF, markdown, or text file) with your answers to the five questions above. Include screenshots where relevant to support your findings.

---

## Notes

- Save your VM configuration—you may want to use it in future labs
- Experiment! The worst that can happen is you need to rebuild the VM
- This is your sandbox environment for learning; breaking things here is safe and instructive