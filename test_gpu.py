# File: test_gpu.py
"""
GPU Test Script
Tests GPU availability and performance
"""

print("="*60)
print("GPU Test Script")
print("="*60 + "\n")

# Test 1: Check if TensorFlow is installed
print("Test 1: TensorFlow Installation")
print("-"*60)
try:
    import tensorflow as tf
    print(f"TensorFlow version: {tf.__version__}")
    print("Status: OK")
except ImportError:
    print("Status: FAILED - TensorFlow not installed")
    print("Install: pip install tensorflow==2.15.0")
    exit(1)

print()

# Test 2: Check CUDA support
print("Test 2: CUDA Support")
print("-"*60)
print(f"Built with CUDA: {tf.test.is_built_with_cuda()}")
print(f"CUDA available: {len(tf.config.list_physical_devices('GPU')) > 0}")

if not tf.test.is_built_with_cuda():
    print("\nWarning: TensorFlow not built with CUDA")
    print("This is normal if CUDA is not installed")
    print("Program will use CPU (works fine, just slower)")

print()

# Test 3: List available devices
print("Test 3: Available Devices")
print("-"*60)
print("CPUs:", tf.config.list_physical_devices('CPU'))
print("GPUs:", tf.config.list_physical_devices('GPU'))

gpus = tf.config.list_physical_devices('GPU')

if gpus:
    print(f"\nGPU detected: {len(gpus)} device(s)")
    for i, gpu in enumerate(gpus):
        print(f"  GPU {i}: {gpu.name}")
else:
    print("\nNo GPU detected")
    print("Using CPU (works fine, just slower)")

print()

# Test 4: Performance test
print("Test 4: Performance Benchmark")
print("-"*60)

import time
import numpy as np

def benchmark_device(device_name):
    """Run a simple benchmark on specified device"""
    print(f"\nTesting on {device_name}...")
    
    with tf.device(device_name):
        # Create large matrices
        a = tf.random.normal([5000, 5000])
        b = tf.random.normal([5000, 5000])
        
        # Warm up
        _ = tf.matmul(a, b)
        
        # Benchmark
        start = time.time()
        for _ in range(10):
            c = tf.matmul(a, b)
        elapsed = time.time() - start
        
        print(f"  10x Matrix multiplication (5000x5000)")
        print(f"  Time: {elapsed:.3f} seconds")
        print(f"  Speed: {10/elapsed:.2f} operations/sec")
    
    return elapsed

# Test CPU
cpu_time = benchmark_device('/CPU:0')

# Test GPU if available
if gpus:
    gpu_time = benchmark_device('/GPU:0')
    speedup = cpu_time / gpu_time
    print(f"\nSpeedup: {speedup:.2f}x faster on GPU")
else:
    print("\nNo GPU to test")

print()

# Test 5: Memory test
print("Test 5: GPU Memory")
print("-"*60)

if gpus:
    try:
        # Try to get memory info
        from src.gpu_config import get_gpu_memory_info
        
        mem_info = get_gpu_memory_info()
        if mem_info:
            print(f"Total: {mem_info['total']:.2f} GB")
            print(f"Used: {mem_info['used']:.2f} GB")
            print(f"Free: {mem_info['free']:.2f} GB")
        else:
            print("Could not get memory info")
            print("Install nvidia-ml-py3 for detailed info:")
            print("  pip install nvidia-ml-py3")
    except:
        print("GPU memory info not available")
else:
    print("No GPU detected")

print()

# Summary
print("="*60)
print("Summary")
print("="*60)

if gpus:
    print("Status: GPU AVAILABLE")
    print(f"Device: {gpus[0].name}")
    print("Performance: GPU acceleration enabled")
    print("\nYour system is ready for GPU-accelerated inference!")
else:
    print("Status: CPU ONLY")
    print("Device: CPU")
    print("Performance: CPU mode (works fine, slower)")
    print("\nTo enable GPU:")
    print("1. Install CUDA 11.8")
    print("2. Install cuDNN 8.6")
    print("3. See CUDA_SETUP.md for details")

print("="*60)