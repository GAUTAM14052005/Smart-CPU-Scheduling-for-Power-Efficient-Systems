"""
Energy-Efficient CPU Scheduling Algorithm
Subject: Operating Systems | B.Tech CSE 2nd Year
Lovely Professional University

Authors:
- Gautam Ahuja (UID: 12410645)
- Jashan (UID: 12418454)
- Pratanu Sinha (UID: 12400483)

Description:
This module implements an energy-efficient CPU scheduling algorithm that minimizes
energy consumption without compromising performance. It's specifically designed for
mobile and embedded systems.
"""

import heapq
from typing import List, Tuple, Dict
from dataclasses import dataclass
from enum import Enum


class CPUFrequency(Enum):
    """CPU Frequency States (in MHz)"""
    LOW = 1200      # Low power state
    MEDIUM = 1800   # Medium power state
    HIGH = 2400     # High performance state


@dataclass
class Process:
    """Represents a process with scheduling parameters"""
    pid: int                    # Process ID
    arrival_time: int          # When process arrives
    burst_time: int            # CPU time needed
    priority: int              # Priority level (1-5, 5 is highest)
    energy_sensitive: bool     # Is process energy-sensitive?
    
    def __lt__(self, other):
        """For heap operations"""
        return self.pid < other.pid
    
    def __repr__(self):
        return f"P{self.pid}(arr:{self.arrival_time}, burst:{self.burst_time}, pri:{self.priority})"


class EnergyEfficientScheduler:
    """
    Energy-Efficient CPU Scheduling Algorithm
    
    Algorithm Overview:
    1. Dynamically scales CPU frequency based on process requirements
    2. Considers process priority and energy sensitivity
    3. Uses adaptive time quantum for time-sharing
    4. Implements DVFS (Dynamic Voltage and Frequency Scaling)
    """
    
    def __init__(self):
        self.current_time = 0
        self.current_frequency = CPUFrequency.MEDIUM
        self.total_energy = 0
        self.completion_times = {}
        self.wait_times = {}
        self.turnaround_times = {}
        self.idle_time = 0
        self.frequency_changes = 0
        
        # Power consumption rates (mW) at different frequencies
        self.power_consumption = {
            CPUFrequency.LOW: 500,      # 500mW at 1.2GHz
            CPUFrequency.MEDIUM: 1200,  # 1200mW at 1.8GHz
            CPUFrequency.HIGH: 2400,    # 2400mW at 2.4GHz
        }
    
    def select_frequency(self, process: Process, ready_queue_size: int) -> CPUFrequency:
        """
        Select optimal frequency based on process characteristics
        
        Strategy:
        - High priority or heavy CPU load → HIGH frequency
        - Normal processes with medium load → MEDIUM frequency
        - Energy-sensitive processes with low load → LOW frequency
        """
        if process.priority >= 4 or (ready_queue_size > 3 and process.burst_time > 10):
            return CPUFrequency.HIGH
        elif process.energy_sensitive and process.burst_time < 5:
            return CPUFrequency.LOW
        else:
            return CPUFrequency.MEDIUM
    
    def schedule(self, processes: List[Process]) -> Dict:
        """
        Main scheduling algorithm using Energy-Aware Round Robin with DVFS
        
        Algorithm:
        1. Sort processes by arrival time
        2. Use ready queue with dynamic time quantum
        3. Scale frequency based on process characteristics
        4. Calculate energy consumption at each step
        """
        # Sort by arrival time
        processes.sort(key=lambda p: p.arrival_time)
        
        ready_queue = []
        completed = []
        schedule_log = []
        
        i = 0
        
        while i < len(processes) or ready_queue:
            # Add processes that have arrived
            while i < len(processes) and processes[i].arrival_time <= self.current_time:
                ready_queue.append(processes[i])
                i += 1
            
            if not ready_queue:
                # CPU idle - skip to next arrival
                if i < len(processes):
                    next_arrival = processes[i].arrival_time
                    idle_duration = next_arrival - self.current_time
                    self.idle_time += idle_duration
                    self.current_time = next_arrival
                    schedule_log.append({
                        'time': self.current_time,
                        'event': 'IDLE',
                        'duration': idle_duration,
                        'energy': 0
                    })
                continue
            
            # Select process with highest priority (ties broken by FCFS)
            ready_queue.sort(key=lambda p: (-p.priority, p.arrival_time))
            current_process = ready_queue.pop(0)
            
            # Select frequency based on current conditions
            selected_freq = self.select_frequency(current_process, len(ready_queue))
            
            # Log frequency change if it occurs
            if selected_freq != self.current_frequency:
                self.frequency_changes += 1
                self.current_frequency = selected_freq
            
            # Calculate dynamic time quantum
            time_quantum = self._calculate_time_quantum(current_process, len(ready_queue))
            
            # Execute process for time quantum or until completion
            execution_time = min(time_quantum, current_process.burst_time)
            
            # Calculate energy consumed
            execution_energy = (self.power_consumption[self.current_frequency] * execution_time) / 1000  # mJ
            self.total_energy += execution_energy
            
            # Update process burst time
            current_process.burst_time -= execution_time
            self.current_time += execution_time
            
            # Log execution
            schedule_log.append({
                'process': current_process.pid,
                'start_time': self.current_time - execution_time,
                'end_time': self.current_time,
                'duration': execution_time,
                'frequency': self.current_frequency.name,
                'frequency_mhz': self.current_frequency.value,
                'power_mw': self.power_consumption[self.current_frequency],
                'energy_mj': execution_energy
            })
            
            # If process not completed, add back to queue
            if current_process.burst_time > 0:
                ready_queue.append(current_process)
            else:
                # Process completed
                self.completion_times[current_process.pid] = self.current_time
                self.turnaround_times[current_process.pid] = self.current_time - current_process.arrival_time
                self.wait_times[current_process.pid] = (self.turnaround_times[current_process.pid] - 
                                                        (processes[current_process.pid-1].burst_time))
                completed.append(current_process)
        
        return self._generate_results(schedule_log, processes)
    
    def _calculate_time_quantum(self, process: Process, queue_size: int) -> int:
        """
        Calculate adaptive time quantum based on process characteristics
        
        Formula: base_quantum + priority_bonus - energy_penalty
        """
        base_quantum = 4  # Base time slice
        priority_bonus = process.priority  # Higher priority gets longer slice
        energy_penalty = 2 if process.energy_sensitive else 0  # Energy-sensitive: shorter slice
        
        quantum = max(1, base_quantum + priority_bonus - energy_penalty)
        
        # Adjust for queue congestion
        if queue_size > 5:
            quantum = max(1, quantum - 1)
        
        return quantum
    
    def _generate_results(self, schedule_log: List[Dict], original_processes: List) -> Dict:
        """Generate comprehensive scheduling results"""
        # Recalculate wait times correctly
        total_burst = {p.pid: p.burst_time for p in original_processes}
        
        # Reset wait times calculation
        self.wait_times = {}
        for pid in self.completion_times:
            arrival_time = next((p.arrival_time for p in original_processes if p.pid == pid), 0)
            burst_time = next((p.burst_time for p in original_processes if p.pid == pid), 0)
            self.wait_times[pid] = self.completion_times[pid] - arrival_time - burst_time
        
        return {
            'schedule_log': schedule_log,
            'total_energy': self.total_energy,
            'total_time': self.current_time,
            'idle_time': self.idle_time,
            'cpu_utilization': ((self.current_time - self.idle_time) / self.current_time * 100) if self.current_time > 0 else 0,
            'frequency_changes': self.frequency_changes,
            'completion_times': self.completion_times,
            'wait_times': self.wait_times,
            'turnaround_times': self.turnaround_times,
            'avg_wait_time': sum(self.wait_times.values()) / len(self.wait_times) if self.wait_times else 0,
            'avg_turnaround_time': sum(self.turnaround_times.values()) / len(self.turnaround_times) if self.turnaround_times else 0,
        }


class FCFSScheduler:
    """First Come First Serve - Baseline for comparison"""
    
    def __init__(self):
        self.current_time = 0
        self.total_energy = 0
        self.completion_times = {}
        self.wait_times = {}
        self.turnaround_times = {}
        self.power_mw = 1500  # Constant power (no frequency scaling)
    
    def schedule(self, processes: List[Process]) -> Dict:
        """Execute FCFS scheduling"""
        original_processes = {p.pid: p.burst_time for p in processes}
        processes_sorted = sorted(processes, key=lambda p: p.arrival_time)
        schedule_log = []
        
        for process in processes_sorted:
            # Wait until process arrives
            self.current_time = max(self.current_time, process.arrival_time)
            start_time = self.current_time
            
            # Execute for entire burst time
            self.current_time += process.burst_time
            
            # Calculate energy
            energy = (self.power_mw * process.burst_time) / 1000
            self.total_energy += energy
            
            # Calculate metrics
            self.completion_times[process.pid] = self.current_time
            self.turnaround_times[process.pid] = self.current_time - process.arrival_time
            self.wait_times[process.pid] = self.turnaround_times[process.pid] - original_processes[process.pid]
            
            schedule_log.append({
                'process': process.pid,
                'start_time': start_time,
                'end_time': self.current_time,
                'duration': process.burst_time,
                'power_mw': self.power_mw
            })
        
        return {
            'schedule_log': schedule_log,
            'total_energy': self.total_energy,
            'total_time': self.current_time,
            'completion_times': self.completion_times,
            'wait_times': self.wait_times,
            'turnaround_times': self.turnaround_times,
            'avg_wait_time': sum(self.wait_times.values()) / len(self.wait_times) if self.wait_times else 0,
            'avg_turnaround_time': sum(self.turnaround_times.values()) / len(self.turnaround_times) if self.turnaround_times else 0,
        }


class RoundRobinScheduler:
    """Round Robin - Another baseline for comparison"""
    
    def __init__(self, time_quantum: int = 4):
        self.time_quantum = time_quantum
        self.current_time = 0
        self.total_energy = 0
        self.completion_times = {}
        self.wait_times = {}
        self.turnaround_times = {}
        self.power_mw = 1500
    
    def schedule(self, processes: List[Process]) -> Dict:
        """Execute Round Robin scheduling"""
        ready_queue = []
        schedule_log = []
        original_burst = {p.pid: p.burst_time for p in processes}
        remaining_burst = {p.pid: p.burst_time for p in processes}
        process_arrival = {p.pid: p.arrival_time for p in processes}
        
        processes_list = processes.copy()
        processes_list.sort(key=lambda p: p.arrival_time)
        
        next_process_idx = 0
        
        while next_process_idx < len(processes_list) or ready_queue:
            # Add newly arrived processes
            while (next_process_idx < len(processes_list) and 
                   processes_list[next_process_idx].arrival_time <= self.current_time):
                ready_queue.append(processes_list[next_process_idx])
                next_process_idx += 1
            
            if not ready_queue:
                if next_process_idx < len(processes_list):
                    self.current_time = processes_list[next_process_idx].arrival_time
                continue
            
            # Get next process from queue
            current_process = ready_queue.pop(0)
            
            # Execute for time quantum or remaining burst
            execution_time = min(self.time_quantum, remaining_burst[current_process.pid])
            
            energy = (self.power_mw * execution_time) / 1000
            self.total_energy += energy
            
            self.current_time += execution_time
            remaining_burst[current_process.pid] -= execution_time
            
            schedule_log.append({
                'process': current_process.pid,
                'start_time': self.current_time - execution_time,
                'end_time': self.current_time,
                'duration': execution_time
            })
            
            # If process not complete, add back to queue
            if remaining_burst[current_process.pid] > 0:
                ready_queue.append(current_process)
            else:
                self.completion_times[current_process.pid] = self.current_time
                self.turnaround_times[current_process.pid] = self.current_time - process_arrival[current_process.pid]
                self.wait_times[current_process.pid] = self.turnaround_times[current_process.pid] - original_burst[current_process.pid]
        
        return {
            'schedule_log': schedule_log,
            'total_energy': self.total_energy,
            'total_time': self.current_time,
            'completion_times': self.completion_times,
            'wait_times': self.wait_times,
            'turnaround_times': self.turnaround_times,
            'avg_wait_time': sum(self.wait_times.values()) / len(self.wait_times) if self.wait_times else 0,
            'avg_turnaround_time': sum(self.turnaround_times.values()) / len(self.turnaround_times) if self.turnaround_times else 0,
        }


def demo_and_compare():
    """Demonstrate the algorithm with example processes"""
    
    # Create test processes
    def create_processes():
        return [
            Process(pid=1, arrival_time=0, burst_time=8, priority=2, energy_sensitive=True),
            Process(pid=2, arrival_time=1, burst_time=4, priority=3, energy_sensitive=False),
            Process(pid=3, arrival_time=2, burst_time=2, priority=1, energy_sensitive=True),
            Process(pid=4, arrival_time=3, burst_time=6, priority=4, energy_sensitive=False),
            Process(pid=5, arrival_time=4, burst_time=3, priority=2, energy_sensitive=True),
        ]
    
    processes = create_processes()
    
    print("=" * 80)
    print("ENERGY-EFFICIENT CPU SCHEDULING ALGORITHM - DEMO")
    print("=" * 80)
    print("\nTest Processes:")
    for p in processes:
        print(f"  {p}")
    
    # Run our energy-efficient scheduler
    print("\n" + "=" * 80)
    print("1. ENERGY-EFFICIENT SCHEDULER WITH DVFS")
    print("=" * 80)
    ee_scheduler = EnergyEfficientScheduler()
    ee_results = ee_scheduler.schedule(create_processes())
    
    print(f"Total Energy Consumed: {ee_results['total_energy']:.2f} mJ")
    print(f"Total Execution Time: {ee_results['total_time']} units")
    print(f"CPU Utilization: {ee_results['cpu_utilization']:.2f}%")
    print(f"Frequency Changes: {ee_results['frequency_changes']}")
    print(f"Average Wait Time: {ee_results['avg_wait_time']:.2f}")
    print(f"Average Turnaround Time: {ee_results['avg_turnaround_time']:.2f}")
    
    # Run FCFS
    print("\n" + "=" * 80)
    print("2. FIRST COME FIRST SERVE (BASELINE)")
    print("=" * 80)
    fcfs_scheduler = FCFSScheduler()
    fcfs_results = fcfs_scheduler.schedule(create_processes())
    
    print(f"Total Energy Consumed: {fcfs_results['total_energy']:.2f} mJ")
    print(f"Total Execution Time: {fcfs_results['total_time']} units")
    print(f"Average Wait Time: {fcfs_results['avg_wait_time']:.2f}")
    print(f"Average Turnaround Time: {fcfs_results['avg_turnaround_time']:.2f}")
    
    # Run Round Robin
    print("\n" + "=" * 80)
    print("3. ROUND ROBIN (BASELINE)")
    print("=" * 80)
    rr_scheduler = RoundRobinScheduler(time_quantum=4)
    rr_results = rr_scheduler.schedule(create_processes())
    
    print(f"Total Energy Consumed: {rr_results['total_energy']:.2f} mJ")
    print(f"Total Execution Time: {rr_results['total_time']} units")
    print(f"Average Wait Time: {rr_results['avg_wait_time']:.2f}")
    print(f"Average Turnaround Time: {rr_results['avg_turnaround_time']:.2f}")
    
    # Comparison
    print("\n" + "=" * 80)
    print("COMPARATIVE ANALYSIS")
    print("=" * 80)
    
    if fcfs_results['total_energy'] > 0:
        energy_savings_vs_fcfs = ((fcfs_results['total_energy'] - ee_results['total_energy']) / 
                                  fcfs_results['total_energy'] * 100)
        print(f"\nEnergy Efficiency vs FCFS: {energy_savings_vs_fcfs:.2f}% energy saved")
    
    if rr_results['total_energy'] > 0:
        energy_savings_vs_rr = ((rr_results['total_energy'] - ee_results['total_energy']) / 
                                rr_results['total_energy'] * 100)
        print(f"Energy Efficiency vs Round Robin: {energy_savings_vs_rr:.2f}% energy saved")
    
    print(f"\nScheduling Quality:")
    print(f"  EE Scheduler - Avg Wait: {ee_results['avg_wait_time']:.2f}, Avg Turnaround: {ee_results['avg_turnaround_time']:.2f}")
    print(f"  FCFS - Avg Wait: {fcfs_results['avg_wait_time']:.2f}, Avg Turnaround: {fcfs_results['avg_turnaround_time']:.2f}")
    print(f"  RR - Avg Wait: {rr_results['avg_wait_time']:.2f}, Avg Turnaround: {rr_results['avg_turnaround_time']:.2f}")
    
    return {
        'ee_results': ee_results,
        'fcfs_results': fcfs_results,
        'rr_results': rr_results,
        'processes': processes
    }


if __name__ == "__main__":
    results = demo_and_compare()
