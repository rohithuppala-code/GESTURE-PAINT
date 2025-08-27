import React, { useState, useEffect, useRef } from 'react';
import { Camera, Hand, Palette, ArrowRight, RotateCcw, AlertCircle, Sparkles } from 'lucide-react';
import io from 'socket.io-client';

const API_BASE = 'http://localhost:5000/api';
const socket = io('http://localhost:5000', {
  reconnectionAttempts: 5,
  timeout: 10000,
  transports: ['websocket']
});

const LandingPage = () => {
  const [showMainApp, setShowMainApp] = useState(false);

  if (showMainApp) {
    return <MainDrawingApp onBack={() => setShowMainApp(false)} />;
  }

  return (
    <div className="min-h-screen w-full bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 overflow-auto">
      {/* Animated background elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-60 h-60 bg-pink-500 rounded-full mix-blend-multiply filter blur-xl opacity-10 animate-pulse"></div>
      </div>

      {/* Hero Section - Full Screen */}
      <div className="relative z-10 min-h-screen flex items-center justify-center py-20">
        <div className="container mx-auto px-6">
          <div className="max-w-6xl mx-auto">
            <div className="grid lg:grid-cols-2 gap-16 items-center">
              
              {/* Left Content */}
              <div className="text-left space-y-8">
                <div className="flex items-center space-x-3 mb-6">
                  <Hand className="h-12 w-12 text-blue-400" />
                  <span className="text-4xl font-bold text-white">GestureDraw</span>
                </div>

                <div className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-full border border-blue-400/30 mb-8">
                  <Sparkles className="h-5 w-5 text-blue-300 mr-2" />
                  <span className="text-blue-300 font-medium">AI-Powered Hand Tracking</span>
                </div>
                
                <h1 className="text-6xl lg:text-7xl font-bold text-white leading-tight">
                  Draw with Your
                  <span className="block text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400">
                    Hands in Air
                  </span>
                </h1>
                
                <p className="text-xl text-gray-300 leading-relaxed max-w-xl">
                  Experience the magic of creating art with just your hand gestures. No tools needed - 
                  just point, draw, and watch your creativity come alive in real-time.
                </p>

                <div className="flex flex-col sm:flex-row gap-6">
                  <button 
                    onClick={() => setShowMainApp(true)}
                    className="group bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 text-white px-10 py-5 rounded-2xl font-bold text-xl hover:shadow-2xl hover:shadow-purple-500/50 transition-all duration-500 transform hover:scale-105"
                  >
                    <span className="flex items-center justify-center">
                      Start Creating Magic
                      <ArrowRight className="ml-3 h-6 w-6 group-hover:translate-x-2 transition-transform duration-300" />
                    </span>
                  </button>
                </div>

                {/* Gesture Preview */}
                <div className="grid grid-cols-5 gap-4 mt-12 p-6 bg-white/5 rounded-2xl backdrop-blur-sm border border-white/10">
                  <div className="text-center">
                    <div className="text-2xl mb-2">☝️</div>
                    <div className="text-xs text-gray-300">Draw</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl mb-2">✌️</div>
                    <div className="text-xs text-gray-300">Hover</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl mb-2">✋</div>
                    <div className="text-xs text-gray-300">Erase</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl mb-2">🤏</div>
                    <div className="text-xs text-gray-300">Resize</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl mb-2">✊</div>
                    <div className="text-xs text-gray-300">Color</div>
                  </div>
                </div>
              </div>

              {/* Right Visual */}
              <div className="relative">
                <div className="relative bg-gradient-to-br from-blue-500/20 via-purple-500/20 to-pink-500/20 p-8 rounded-3xl backdrop-blur-sm border border-white/20 shadow-2xl">
                  <div className="aspect-video bg-gray-900/50 rounded-2xl flex items-center justify-center relative overflow-hidden">
                    <div className="absolute inset-0 bg-gradient-to-br from-blue-900/20 to-purple-900/20"></div>
                    <div className="relative z-10 text-center">
                      <div className="animate-bounce mb-4">
                        <Hand className="h-20 w-20 text-blue-400 mx-auto" />
                      </div>
                      <h3 className="text-2xl font-bold text-white mb-2">Live Camera Magic</h3>
                      <p className="text-gray-300">Your hands will appear here</p>
                      <div className="mt-6 flex justify-center space-x-2">
                        <div className="w-3 h-3 bg-blue-400 rounded-full animate-pulse"></div>
                        <div className="w-3 h-3 bg-purple-400 rounded-full animate-pulse"></div>
                        <div className="w-3 h-3 bg-pink-400 rounded-full animate-pulse"></div>
                      </div>
                    </div>
                  </div>
                  
                  {/* Floating color palette preview */}
                  <div className="absolute -bottom-4 -right-4 bg-white/10 backdrop-blur-md rounded-xl p-3 border border-white/20">
                    <div className="flex space-x-2">
                      <div className="w-4 h-4 bg-red-500 rounded-full"></div>
                      <div className="w-4 h-4 bg-green-500 rounded-full"></div>
                      <div className="w-4 h-4 bg-blue-500 rounded-full"></div>
                      <div className="w-4 h-4 bg-yellow-400 rounded-full"></div>
                      <div className="w-4 h-4 bg-purple-500 rounded-full"></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Features Strip */}
      <div className="relative z-10 py-20 bg-black/20 backdrop-blur-sm border-t border-white/10">
        <div className="container mx-auto px-6">
          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            <div className="text-center group hover:scale-105 transition-transform duration-300">
              <div className="bg-gradient-to-br from-blue-500/20 to-blue-600/20 w-20 h-20 rounded-2xl flex items-center justify-center mx-auto mb-6 group-hover:from-blue-500/30 group-hover:to-blue-600/30 transition-all duration-300">
                <Sparkles className="h-10 w-10 text-blue-400" />
              </div>
              <h3 className="text-2xl font-bold text-white mb-3">Instant Response</h3>
              <p className="text-gray-300">Real-time hand tracking with zero lag</p>
            </div>

            <div className="text-center group hover:scale-105 transition-transform duration-300">
              <div className="bg-gradient-to-br from-purple-500/20 to-purple-600/20 w-20 h-20 rounded-2xl flex items-center justify-center mx-auto mb-6 group-hover:from-purple-500/30 group-hover:to-purple-600/30 transition-all duration-300">
                <Palette className="h-10 w-10 text-purple-400" />
              </div>
              <h3 className="text-2xl font-bold text-white mb-3">6 Magic Colors</h3>
              <p className="text-gray-300">Switch with simple gestures</p>
            </div>

            <div className="text-center group hover:scale-105 transition-transform duration-300">
              <div className="bg-gradient-to-br from-pink-500/20 to-pink-600/20 w-20 h-20 rounded-2xl flex items-center justify-center mx-auto mb-6 group-hover:from-pink-500/30 group-hover:to-pink-600/30 transition-all duration-300">
                <Hand className="h-10 w-10 text-pink-400" />
              </div>
              <h3 className="text-2xl font-bold text-white mb-3">Natural Gestures</h3>
              <p className="text-gray-300">Intuitive hand movements</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const MainDrawingApp = ({ onBack }) => {
  const [cameraActive, setCameraActive] = useState(false);
  const [drawingState, setDrawingState] = useState({
    gesture: 'Ready',
    color: 'Red',
    brush_size: 5,
    drawing: false
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const canvasRef = useRef(null);
  const frameQueue = useRef([]);
  const lastUpdate = useRef(0);

  const colors = [
    { name: 'Red', bg: 'bg-red-500', active: drawingState.color === 'Red' },
    { name: 'Green', bg: 'bg-green-500', active: drawingState.color === 'Green' },
    { name: 'Blue', bg: 'bg-blue-500', active: drawingState.color === 'Blue' },
    { name: 'Black', bg: 'bg-gray-900', active: drawingState.color === 'Black' },
    { name: 'Yellow', bg: 'bg-yellow-400', active: drawingState.color === 'Yellow' },
    { name: 'Orange', bg: 'bg-orange-500', active: drawingState.color === 'Orange' },
  ];

  useEffect(() => {
    const renderFrame = () => {
      if (frameQueue.current.length === 0) return;
      
      const { frame, state } = frameQueue.current.shift();
      const canvas = canvasRef.current;
      if (!canvas) return;

      const ctx = canvas.getContext('2d');
      const img = new Image();
      img.src = frame;
      img.onload = () => {
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        if (Date.now() - lastUpdate.current > 50) { // Update state every 50ms
          setDrawingState(state);
          lastUpdate.current = Date.now();
        }
      };
      img.onerror = () => {
        console.error('Failed to load frame image');
        setError('Failed to render camera feed');
      };
    };

    socket.on('connect', () => {
      console.log('WebSocket connected successfully');
      setError('');
    });

    socket.on('connect_error', (err) => {
      console.error('WebSocket connection error:', err.message);
      setError(`WebSocket connection failed: ${err.message}`);
    });

    socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
      setCameraActive(false);
      frameQueue.current = [];
      setError('WebSocket disconnected. Please check the server.');
    });

    socket.on('frame_update', (data) => {
      frameQueue.current.push(data);
      if (frameQueue.current.length > 3) frameQueue.current.shift(); // Limit queue to avoid backlog
      renderFrame();
    });

    socket.on('stream_status', (data) => {
      console.log('Stream status update:', data);
      setCameraActive(data.active);
      if (!data.active) {
        frameQueue.current = [];
        const canvas = canvasRef.current;
        if (canvas) {
          canvas.getContext('2d').clearRect(0, 0, canvas.width, canvas.height);
        }
      }
    });

    return () => {
      socket.off('connect');
      socket.off('connect_error');
      socket.off('disconnect');
      socket.off('frame_update');
      socket.off('stream_status');
    };
  }, []);

  const startCamera = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${API_BASE}/start_camera`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      const data = await response.json();
      if (response.ok) {
        setCameraActive(true);
        socket.emit('start_stream');
        console.log('Camera started, initiating WebSocket stream');
      } else {
        setError(`${data.error || 'Failed to start camera'}: ${data.details || 'No details provided'}`);
        console.error('Camera start failed:', data);
      }
    } catch (err) {
      setError('Network error: Ensure Flask server is running on localhost:5000');
      console.error('Network error starting camera:', err.message);
    }
    setLoading(false);
  };

  const stopCamera = async () => {
    try {
      socket.emit('stop_stream');
      const response = await fetch(`${API_BASE}/stop_camera`, { method: 'POST' });
      const data = await response.json();
      if (response.ok) {
        setCameraActive(false);
        frameQueue.current = [];
        const canvas = canvasRef.current;
        if (canvas) {
          canvas.getContext('2d').clearRect(0, 0, canvas.width, canvas.height);
        }
        console.log('Camera stopped successfully');
      } else {
        setError(`${data.error || 'Failed to stop camera'}: ${data.details || 'No details provided'}`);
        console.error('Camera stop failed:', data);
      }
    } catch (err) {
      setError('Failed to stop camera: Network error');
      console.error('Error stopping camera:', err.message);
    }
  };

  const clearCanvas = async () => {
    try {
      const response = await fetch(`${API_BASE}/clear_canvas`, { method: 'POST' });
      if (!response.ok) {
        const data = await response.json();
        setError(data.error || 'Failed to clear canvas');
      }
    } catch (err) {
      setError('Failed to clear canvas: Network error');
      console.error('Error clearing canvas:', err.message);
    }
  };

  const setColor = async (colorName) => {
    try {
      const response = await fetch(`${API_BASE}/set_color`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ color: colorName })
      });
      if (!response.ok) {
        const data = await response.json();
        setError(data.error || 'Failed to set color');
      }
    } catch (err) {
      setError('Failed to set color: Network error');
      console.error('Error setting color:', err.message);
    }
  };

  return (
    <div className="fixed inset-0 w-full h-full bg-gradient-to-br from-slate-900 to-slate-800 overflow-hidden">
      {/* Header */}
      <nav className="absolute top-0 left-0 right-0 z-20 bg-black/30 backdrop-blur-md border-b border-white/10">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button 
                onClick={onBack}
                className="text-gray-300 hover:text-white transition-colors px-4 py-2 rounded-lg hover:bg-white/10"
              >
                ← Back to Home
              </button>
              <div className="flex items-center space-x-3">
                <Hand className="h-8 w-8 text-blue-400" />
                <span className="text-2xl font-bold text-white">GestureDraw</span>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className={`w-3 h-3 rounded-full ${cameraActive ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`}></div>
                <span className={`text-sm font-medium ${cameraActive ? 'text-green-400' : 'text-red-400'}`}>
                  {cameraActive ? 'Live' : 'Offline'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="pt-20 h-full">
        {/* Error Message */}
        {error && (
          <div className="absolute top-24 left-6 right-6 z-10 p-4 bg-red-500/20 border border-red-500/30 rounded-lg flex items-center space-x-2">
            <AlertCircle className="h-5 w-5 text-red-400" />
            <span className="text-red-300">{error}</span>
          </div>
        )}

        <div className="h-full flex">
          
          {/* Compact Sidebar */}
          <div className="w-80 p-6 space-y-4 bg-black/20 backdrop-blur-sm border-r border-white/10 overflow-y-auto">
            
            {/* Camera Controls */}
            <div className="bg-white/5 backdrop-blur-sm rounded-xl p-4 border border-white/10">
              <h3 className="text-lg font-semibold text-white mb-3 flex items-center">
                <Camera className="h-5 w-5 mr-2 text-blue-400" />
                Camera
              </h3>
              
              {!cameraActive ? (
                <button 
                  onClick={startCamera}
                  disabled={loading}
                  className="w-full bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 disabled:from-gray-600 disabled:to-gray-700 text-white py-3 rounded-lg font-medium transition-all duration-300 transform hover:scale-105"
                >
                  {loading ? 'Starting...' : 'Start Magic ✨'}
                </button>
              ) : (
                <button 
                  onClick={stopCamera}
                  className="w-full bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 text-white py-3 rounded-lg font-medium transition-all duration-300"
                >
                  Stop Camera
                </button>
              )}
            </div>
            
            {/* Current Gesture */}
            <div className="bg-white/5 backdrop-blur-sm rounded-xl p-4 border border-white/10">
              <h3 className="text-lg font-semibold text-white mb-3">Current Gesture</h3>
              <div className="text-center">
                <div className="px-4 py-3 bg-gradient-to-r from-blue-500/20 to-purple-500/20 text-blue-300 rounded-xl font-bold text-lg border border-blue-400/30">
                  {drawingState.gesture}
                </div>
              </div>
            </div>

            {/* Color Palette */}
            <div className="bg-white/5 backdrop-blur-sm rounded-xl p-4 border border-white/10">
              <h3 className="text-lg font-semibold text-white mb-3 flex items-center">
                <Palette className="h-5 w-5 mr-2 text-purple-400" />
                Colors
              </h3>
              
              <div className="grid grid-cols-3 gap-2 mb-3">
                {colors.map((color) => (
                  <button
                    key={color.name}
                    onClick={() => setColor(color.name)}
                    className={`${color.bg} w-full h-10 rounded-lg transition-all duration-200 ${
                      color.active 
                        ? 'ring-2 ring-white scale-110 shadow-lg' 
                        : 'hover:scale-105'
                    }`}
                    title={color.name}
                  />
                ))}
              </div>
              
              <div className="text-center p-2 bg-white/5 rounded-lg">
                <span className="text-sm text-gray-300">Active: </span>
                <span className="text-sm font-bold text-white">{drawingState.color}</span>
              </div>
            </div>

            {/* Brush Size */}
            <div className="bg-white/5 backdrop-blur-sm rounded-xl p-4 border border-white/10">
              <h3 className="text-lg font-semibold text-white mb-3">Brush Size</h3>
              
              <div className="text-center">
                <div className="flex justify-center mb-3">
                  <div className="bg-white rounded-full" style={{
                    width: `${Math.max(drawingState.brush_size * 2, 8)}px`,
                    height: `${Math.max(drawingState.brush_size * 2, 8)}px`
                  }}></div>
                </div>
                <span className="text-2xl font-bold text-white">{drawingState.brush_size}px</span>
                <p className="text-xs text-gray-400 mt-1">Use pinch gesture</p>
              </div>
            </div>

            {/* Clear Canvas */}
            <div className="bg-white/5 backdrop-blur-sm rounded-xl p-4 border border-white/10">
              <button 
                onClick={clearCanvas}
                className="w-full bg-gradient-to-r from-red-500/20 to-red-600/20 hover:from-red-500/30 hover:to-red-600/30 text-red-300 py-3 rounded-lg font-medium transition-all duration-300 border border-red-500/30"
              >
                <RotateCcw className="h-4 w-4 inline mr-2" />
                Clear Canvas
              </button>
            </div>
          </div>

          {/* Main Camera Area - Full Height */}
          <div className="flex-1 p-4">
            <div className="bg-gradient-to-br from-blue-500/5 to-purple-500/5 rounded-2xl p-4 h-full border border-white/10 backdrop-blur-sm">
              <div className="bg-black rounded-xl h-full relative overflow-hidden">
                {cameraActive ? (
                  <canvas
                    ref={canvasRef}
                    className="w-full h-full object-cover rounded-lg"
                    width={640}
                    height={480}
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-900 to-gray-800">
                    <div className="text-center">
                      <div className="animate-pulse mb-6">
                        <Camera className="h-24 w-24 text-gray-500 mx-auto" />
                      </div>
                      <h3 className="text-2xl font-semibold text-gray-400 mb-2">
                        Ready to Draw
                      </h3>
                      <p className="text-gray-500 text-lg">
                        Click "Start Magic" to begin your creative journey
                      </p>
                    </div>
                  </div>
                )}

                {/* Floating Status Indicators */}
                {cameraActive && (
                  <>
                    <div className="absolute top-4 left-4">
                      <div className="bg-black/70 backdrop-blur-sm rounded-lg px-4 py-2 border border-white/20">
                        <span className="text-white font-medium">✋ {drawingState.gesture}</span>
                      </div>
                    </div>

                    <div className="absolute top-4 right-4 space-y-2">
                      <div className="bg-black/70 backdrop-blur-sm rounded-lg px-3 py-2 text-right border border-white/20">
                        <div className="text-xs text-gray-300">Color</div>
                        <div className="text-white font-bold">{drawingState.color}</div>
                      </div>
                      <div className="bg-black/70 backdrop-blur-sm rounded-lg px-3 py-2 text-right border border-white/20">
                        <div className="text-xs text-gray-300">Size</div>
                        <div className="text-white font-bold">{drawingState.brush_size}px</div>
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LandingPage;