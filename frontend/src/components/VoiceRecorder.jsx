import React, { useState, useRef, useEffect, useContext } from 'react';
import { RefreshContext } from '../context/RefreshContext';
import { quickLog, guidedLogStart, guidedLogFinalize } from '../api/client';
import './VoiceRecorder.css';

function VoiceRecorder({ mode }) {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [manualText, setManualText] = useState('');
  const [isTypeMode, setIsTypeMode] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [recordingTime, setRecordingTime] = useState(0);
  const [showWarning, setShowWarning] = useState(false);
  
  // Guided mode state
  const [guidedState, setGuidedState] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState([]);
  
  const recognitionRef = useRef(null);
  const timerRef = useRef(null);
  const activeStreamRef = useRef(null);
  const retryCountRef = useRef(0);
  const { triggerRefresh } = useContext(RefreshContext);

  // Initialize Web Speech API
  useEffect(() => {
    console.log('🎤 Initializing Web Speech API');
    console.log('Browser:', navigator.userAgent);
    console.log('Has SpeechRecognition:', 'SpeechRecognition' in window);
    console.log('Has webkitSpeechRecognition:', 'webkitSpeechRecognition' in window);

    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      setError('Web Speech API is not supported in this browser. Please use Chrome or Edge.');
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    console.log('✓ Web Speech API initialized');

    recognition.onstart = () => {
      console.log('🔴 Recording started - listening for audio');
    };

    recognition.onresult = (event) => {
      console.log('📝 Got result event:', event.results.length, 'results');
      let interimTranscript = '';
      let finalTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcriptPiece = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcriptPiece + ' ';
        } else {
          interimTranscript += transcriptPiece;
        }
      }

      setTranscript(prev => {
        const updated = prev + finalTranscript;
        return updated || interimTranscript;
      });
    };

    recognition.onerror = (event) => {
      console.error('❌ Speech recognition error:', event.error);
      
      // Retry on network errors up to 3 times
      if (event.error === 'network' && retryCountRef.current < 3) {
        retryCountRef.current++;
        console.log(`Network error, retrying... (${retryCountRef.current}/3)`);
        setError(`Network issue, retrying... (${retryCountRef.current}/3)`);
        
        setTimeout(() => {
          try {
            recognitionRef.current?.start();
          } catch (e) {
            console.log('Retry failed:', e);
          }
        }, 500);
        return;
      }
      
      if (event.error === 'no-speech') {
        console.warn('⚠️ No speech detected - microphone may not be working or browser may not support it well');
        setError('No speech detected. Please try again. (Check mic permissions & browser support)');
      } else if (event.error === 'not-allowed') {
        setError('Microphone access denied. Please allow microphone access.');
      } else if (event.error === 'network') {
        setError('Network error after 3 retries. Please check your internet connection and try again.');
      } else {
        setError(`Recognition error: ${event.error}`);
      }
      stopRecording();
    };

    recognition.onend = () => {
      // Auto-restart if we're still supposed to be recording
      // This handles the browser's auto-stop behavior
      if (isRecording && recordingTime < 30) {
        try {
          recognition.start();
        } catch (e) {
          console.log('Recognition already stopped');
        }
      }
    };

    recognitionRef.current = recognition;

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      if (activeStreamRef.current) {
        activeStreamRef.current.getTracks().forEach(track => track.stop());
        activeStreamRef.current = null;
      }
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, []);

  // Recording timer
  useEffect(() => {
    if (isRecording) {
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => {
          const newTime = prev + 1;
          
          // Show warning at 25 seconds
          if (newTime === 25) {
            setShowWarning('Still recording...');
          }
          
          // Show stronger warning at 28 seconds
          if (newTime === 28) {
            setShowWarning('Please tap Stop to submit');
          }
          
          return newTime;
        });
      }, 1000);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      setRecordingTime(0);
      setShowWarning(false);
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [isRecording]);

  const ensureMicrophonePermission = async () => {
    // Log what we're detecting for debugging
    console.log('Checking mic API availability...');
    console.log('navigator.mediaDevices:', navigator.mediaDevices);
    console.log('navigator.mediaDevices?.getUserMedia:', navigator.mediaDevices?.getUserMedia);

    // Try to get microphone access directly
    // Some browsers require this to trigger the permission prompt
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      activeStreamRef.current = stream;
      console.log('Microphone access granted');
      return;
    } catch (error) {
      console.error('Microphone access error:', error.name, error.message);
      
      if (error.name === 'NotAllowedError') {
        throw new Error('Microphone permission denied. Click the lock icon in the address bar → Site permissions → Microphone → Allow, then try again.');
      }

      if (error.name === 'SecurityError') {
        throw new Error('Microphone access blocked by browser security. Try https:// or check your site permissions in the lock icon.');
      }

      if (error.name === 'NotFoundError') {
        throw new Error('No microphone was found on this device.');
      }

      if (error.name === 'NotReadableError' || error.message?.includes('Could not start audio source')) {
        throw new Error('Microphone is in use by another application. Close other apps using the mic and try again.');
      }

      throw new Error(`Microphone error: ${error.name}. ${error.message}`);
    }
  };

  const startRecording = async () => {
    console.log('📢 startRecording called');
    setError(null);
    setResult(null);
    setTranscript('');
    setRecordingTime(0);
    setShowWarning(false);
    retryCountRef.current = 0; // Reset retry counter

    const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    const shouldSkipMicPreflight = !window.isSecureContext && !isLocalhost;
    console.log('isLocalhost:', isLocalhost, 'shouldSkipMicPreflight:', shouldSkipMicPreflight);

    try {
      if (!shouldSkipMicPreflight) {
        console.log('🔐 Requesting microphone permission...');
        await ensureMicrophonePermission();
      } else {
        console.warn('Skipping getUserMedia preflight on non-secure origin; attempting SpeechRecognition directly.');
      }
      console.log('✓ Permissions OK, starting speech recognition');
      setIsRecording(true);
      recognitionRef.current?.start();
    } catch (e) {
      console.error('Failed to start recording:', e);
      setError(e.message || 'Failed to start recording. Please try again.');
      setIsRecording(false);
    }
  };

  const stopRecording = () => {
    setIsRecording(false);
    setShowWarning(false);
    
    try {
      recognitionRef.current?.stop();
    } catch (e) {
      console.log('Recognition already stopped');
    }
    
    if (timerRef.current) {
      clearInterval(timerRef.current);
    }

    if (activeStreamRef.current) {
      activeStreamRef.current.getTracks().forEach(track => track.stop());
      activeStreamRef.current = null;
    }
  };

  const submitLog = async (inputText) => {
    if (!inputText.trim()) {
      setError('No speech detected. Please try again.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      if (mode === 'quick') {
        const response = await quickLog(inputText);
        setResult(response);
        triggerRefresh();
      } else {
        const response = await guidedLogStart(inputText);
        setGuidedState(response);
        setCurrentQuestion(0);
        setAnswers([]);
      }
    } catch (err) {
      console.error('Log failed:', err);
      setError(err.message || 'Failed to process your log. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleStopAndSubmit = async () => {
    stopRecording();
    await submitLog(transcript);
  };

  const handleTryAgain = () => {
    setError(null);

    if (transcript.trim()) {
      handleStopAndSubmit();
      return;
    }

    startRecording();
  };

  const handleTypeInstead = () => {
    setError(null);
    setResult(null);
    setIsTypeMode(true);
    setManualText(transcript);
  };

  const handleSubmitTyped = async () => {
    await submitLog(manualText);
  };

  const handleCancelTyped = () => {
    setIsTypeMode(false);
    setManualText('');
  };

  const handleGuidedAnswer = async (answer) => {
    const newAnswers = [...answers, answer];
    setAnswers(newAnswers);

    if (currentQuestion < guidedState.questions.length - 1) {
      setCurrentQuestion(prev => prev + 1);
    } else {
      // All questions answered, finalize
      setIsLoading(true);
      try {
        const response = await guidedLogFinalize(guidedState.extracted_state, newAnswers);
        setResult(response);
        setGuidedState(null);
        triggerRefresh(); // Trigger refresh for dashboard/history
      } catch (err) {
        console.error('Guided finalize failed:', err);
        setError(err.message || 'Failed to finalize log. Please try again.');
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleReset = () => {
    setTranscript('');
    setManualText('');
    setIsTypeMode(false);
    setResult(null);
    setError(null);
    setGuidedState(null);
    setCurrentQuestion(0);
    setAnswers([]);
  };

  // Success state
  if (result) {
    return (
      <div className="voice-recorder success">
        <div className="success-message">
          <h2>✅ Logged!</h2>
          <div className="result-summary">
            {result.symptoms && (
              <div className="result-item">
                <strong>Symptoms:</strong> {result.symptoms.join(' · ')}
              </div>
            )}
            {result.severity !== null && result.severity !== undefined && (
              <div className="result-item">
                <strong>Severity:</strong> {result.severity}/10
              </div>
            )}
            {result.potential_triggers && result.potential_triggers.length > 0 && (
              <div className="result-item">
                <strong>Triggers:</strong> {result.potential_triggers.join(' · ')}
              </div>
            )}
          </div>
        </div>
        <button className="reset-button" onClick={handleReset}>
          Log Another
        </button>
      </div>
    );
  }

  // Guided mode - showing questions
  if (guidedState && !result) {
    const question = guidedState.questions[currentQuestion];
    return (
      <div className="voice-recorder guided">
        <h3>Follow-up Question {currentQuestion + 1}/{guidedState.questions.length}</h3>
        <p className="question">{question}</p>
        <input
          type="text"
          placeholder="Type your answer..."
          onKeyPress={(e) => {
            if (e.key === 'Enter' && e.target.value.trim()) {
              handleGuidedAnswer(e.target.value.trim());
              e.target.value = '';
            }
          }}
        />
        <p className="hint">Press Enter to submit</p>
      </div>
    );
  }

  return (
    <div className="voice-recorder">
      {error && (
        <div className="error-message">
          <p>{error}</p>
          <div className="error-actions">
            <button onClick={handleTryAgain}>Try Again</button>
            <button onClick={handleTypeInstead}>Type Instead</button>
          </div>
        </div>
      )}

      {!isRecording && !isLoading && !error && (
        <div className="recorder-idle">
          <p className="instructions">
            {mode === 'quick' 
              ? 'Tap the mic to describe your symptoms'
              : 'Tap the mic to start. We\'ll ask follow-up questions.'}
          </p>
        </div>
      )}

      {isRecording && (
        <div className="recorder-active">
          <div className="recording-indicator">
            <span className="pulse"></span>
            Recording... {recordingTime}s
          </div>
          {showWarning && (
            <div className="recording-warning">{showWarning}</div>
          )}
          <div className="live-transcript">
            {transcript || 'Listening...'}
          </div>
        </div>
      )}

      {isLoading && (
        <div className="loading">
          <div className="spinner"></div>
          <p>Processing your log...</p>
        </div>
      )}

      {isTypeMode && !isLoading && (
        <div className="typed-input">
          <strong>Type your symptoms</strong>
          <textarea
            value={manualText}
            onChange={(e) => setManualText(e.target.value)}
            placeholder="Example: I’ve had a headache since lunch, severity 7 out of 10, maybe from too much coffee"
            rows={5}
          />
          <div className="typed-actions">
            <button className="submit-button" onClick={handleSubmitTyped}>
              Submit Typed Log
            </button>
            <button className="cancel-button" onClick={handleCancelTyped}>
              Cancel
            </button>
          </div>
        </div>
      )}

      <div className="controls">
        {!isRecording && !isLoading && !isTypeMode && (
          <button 
            className="mic-button" 
            onClick={startRecording}
          >
            🎤
          </button>
        )}

        {isRecording && (
          <button 
            className="stop-button" 
            onClick={handleStopAndSubmit}
          >
            Stop & Submit
          </button>
        )}
      </div>

      {transcript && !isRecording && !isLoading && !error && !isTypeMode && (
        <div className="transcript-preview">
          <strong>Your recording:</strong>
          <p>{transcript}</p>
          <button className="submit-button" onClick={handleStopAndSubmit}>
            Submit
          </button>
        </div>
      )}
    </div>
  );
}

export default VoiceRecorder;
