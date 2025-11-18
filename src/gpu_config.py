# File: src/gpu_config.py
"""
GPU Configuration and Management
Automatically detects and configures GPU/CPU for optimal performance
"""
import os
import warnings
from pathlib import Path
import urllib.request

# Suppress TensorFlow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
warnings.filterwarnings('ignore')


def configure_gpu():
    """
    Configure GPU settings for TensorFlow
    Falls back to CPU if GPU not available
    
    Returns:
        dict: GPU configuration info
    """
    config = {
        'gpu_available': False,
        'gpu_name': None,
        'gpu_memory': None,
        'using_gpu': False,
        'device': 'CPU'
    }
    
    try:
        import tensorflow as tf
        
        # Get GPU devices
        gpus = tf.config.list_physical_devices('GPU')
        
        if gpus:
            config['gpu_available'] = True
            config['gpu_name'] = gpus[0].name
            
            try:
                # Enable memory growth (don't allocate all GPU memory at once)
                for gpu in gpus:
                    tf.config.experimental.set_memory_growth(gpu, True)
                
                # Set visible devices
                tf.config.set_visible_devices(gpus, 'GPU')
                
                config['using_gpu'] = True
                config['device'] = 'GPU'
                
                print(f"✅ GPU detected and configured: {gpus[0].name}")
                print("✅ Memory growth enabled - GPU will allocate memory as needed")
                
            except RuntimeError as e:
                print(f"⚠️ GPU configuration warning: {e}")
                print("⚠️ Falling back to CPU")
                config['using_gpu'] = False
                config['device'] = 'CPU'
        
        else:
            print("ℹ️ No GPU detected")
            print("ℹ️ Using CPU (consider installing CUDA for GPU acceleration)")
            
    except ImportError:
        print("⚠️ TensorFlow not available yet")
    
    except Exception as e:
        print(f"⚠️ GPU configuration error: {e}")
        print("⚠️ Using CPU")
    
    return config


def download_yolo_face_model(models_dir: Path) -> bool:
    """
    Download YOLO face detection model
    
    Args:
        models_dir: Directory to save model
    
    Returns:
        True if successful, False otherwise
    """
    model_path = models_dir / "yolov8n-face.pt"
    
    if model_path.exists():
        print(f"✅ YOLO face model already exists: {model_path}")
        return True
    
    print("📥 Downloading YOLO face detection model...")
    
    # Try multiple sources
    sources = [
        # Option 1: GitHub release (if available)
        "https://github.com/akanametov/yolov8-face/releases/download/v1.0/yolov8n-face.pt",
        
        # Option 2: Hugging Face (alternative)
        "https://huggingface.co/Bingsu/yolov8n-face/resolve/main/yolov8n-face.pt",
    ]
    
    for url in sources:
        try:
            print(f"  Trying: {url}")
            urllib.request.urlretrieve(url, model_path)
            
            # Verify file size (should be > 1MB)
            if model_path.stat().st_size > 1_000_000:
                print(f"✅ YOLO face model downloaded successfully!")
                return True
            else:
                print(f"⚠️ Downloaded file too small, trying next source...")
                model_path.unlink()
                
        except Exception as e:
            print(f"⚠️ Failed to download from {url}: {e}")
            if model_path.exists():
                model_path.unlink()
    
    print("❌ Could not download YOLO face model from any source")
    print("ℹ️ Will fallback to MediaPipe face detection")
    return False


def check_yolo_available(models_dir: Path) -> bool:
    """
    Check if YOLO face detection is available
    
    Args:
        models_dir: Models directory
    
    Returns:
        True if YOLO can be used
    """
    # Check if model exists
    model_path = models_dir / "yolov8n-face.pt"
    if not model_path.exists():
        print("ℹ️ YOLO face model not found")
        return False
    
    # Check if ultralytics is installed
    try:
        import ultralytics
        return True
    except ImportError:
        print("⚠️ Ultralytics not installed (pip install ultralytics)")
        return False


def get_gpu_memory_info():
    """
    Get current GPU memory usage
    
    Returns:
        dict: Memory info or None if GPU not available
    """
    try:
        import tensorflow as tf
        
        gpus = tf.config.list_physical_devices('GPU')
        if not gpus:
            return None
        
        # This requires nvidia-ml-py3
        try:
            import pynvml
            
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            
            return {
                'total': info.total / 1024**3,  # GB
                'used': info.used / 1024**3,    # GB
                'free': info.free / 1024**3     # GB
            }
        except:
            return None
            
    except:
        return None


def optimize_for_inference():
    """
    Optimize TensorFlow for inference (not training)
    """
    try:
        import tensorflow as tf
        
        # Disable debugging
        tf.debugging.set_log_device_placement(False)
        
        # Enable XLA (Accelerated Linear Algebra)
        # This can speed up inference
        # tf.config.optimizer.set_jit(True)  # Uncomment if needed
        
    except:
        pass


def print_device_info():
    """Print detailed device information"""
    print("\n" + "="*60)
    print("Device Configuration")
    print("="*60)
    
    config = configure_gpu()
    
    print(f"Device: {config['device']}")
    print(f"GPU Available: {config['gpu_available']}")
    
    if config['gpu_available']:
        print(f"GPU Name: {config['gpu_name']}")
        print(f"Using GPU: {config['using_gpu']}")
        
        mem_info = get_gpu_memory_info()
        if mem_info:
            print(f"GPU Memory: {mem_info['total']:.2f} GB total")
            print(f"            {mem_info['used']:.2f} GB used")
            print(f"            {mem_info['free']:.2f} GB free")
    
    print("="*60 + "\n")
    
    return config


# Configure on import
GPU_CONFIG = configure_gpu()
optimize_for_inference()


if __name__ == "__main__":
    print_device_info()
    
    # Test TensorFlow
    try:
        import tensorflow as tf
        
        print("\nTensorFlow Test:")
        print(f"TensorFlow version: {tf.__version__}")
        print(f"Built with CUDA: {tf.test.is_built_with_cuda()}")
        
        # Simple computation test
        with tf.device('/GPU:0' if GPU_CONFIG['using_gpu'] else '/CPU:0'):
            a = tf.constant([[1.0, 2.0], [3.0, 4.0]])
            b = tf.constant([[1.0, 1.0], [0.0, 1.0]])
            c = tf.matmul(a, b)
            print(f"\n✅ Test computation successful on {GPU_CONFIG['device']}")
        
    except Exception as e:
        print(f"\n❌ TensorFlow test error: {e}")