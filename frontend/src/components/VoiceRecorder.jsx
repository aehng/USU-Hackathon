import React, { useState, useRef, useEffect, useContext } from 'react';
import { RefreshContext } from '../context/RefreshContext';
import { quickLog, guidedLogStart, guidedLogFinalize, transcribeAudio } from '../api/client';
import './VoiceRecorder.css';

function VoiceRecorder({ mode }) {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [manualText, setManualText] = useState('');
  const [isTypeMode, setIsTypeMode] = useState(false);
  const [inputMethod, setInputMethod] = useState('voice'); // 'voice' or 'type'
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
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerRef = useRef(null);
  const activeStreamRef = useRef(null);
  const retryCountRef = useRef(0);
  const { triggerRefresh } = useContext(RefreshContext);

  // Initialize MediaRecorder (no longer using Web Speech API)
  useEffect(() => {
    console.log('🎤 VoiceRecorder mounted - using Faster-Whisper via MediaRecorder');
    console.log('Browser:', navigator.userAgent);
    console.log('Has MediaRecorder:', 'MediaRecorder' in window);
    console.log('Has mediaDevices:', 'mediaDevices' in navigator);

    if (!('MediaRecorder' in window)) {
      setError('Audio recording is not supported in this browser. Please use Chrome, Edge, or Firefox.');
      return;
    }

    return () => {
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
    setTranscript('🎤 Recording... (speak now)');
    setRecordingTime(0);
    setShowWarning(false);
    retryCountRef.current = 0;
    audioChunksRef.current = [];

    try {
      console.log('🔐 Requesting microphone permission...');
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      activeStreamRef.current = stream;
      console.log('✅ Microphone access granted');

      // Create MediaRecorder
      const mimeType = MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/ogg';
      const mediaRecorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        console.log('🛑 MediaRecorder stopped, processing audio...');
        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });
        console.log('📦 Audio blob created:', audioBlob.size, 'bytes');

        setTranscript('🔄 Transcribing audio...');
        
        try {
          const result = await transcribeAudio(audioBlob);
          const transcribedText = result.text || '';
          console.log('✅ Transcription received:', transcribedText);
          setTranscript(transcribedText);
          
          // Auto-submit after transcription
          if (transcribedText.trim()) {
            await submitLog(transcribedText);
          } else {
            setError('No speech detected in the recording. Please try again.');
          }
        } catch (err) {
          console.error('❌ Transcription failed:', err);
          setError(`Transcription failed: ${err.message}`);
          setTranscript('');
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
      console.log('🔴 Recording started');
    } catch (error) {
      console.error('❌ Failed to start recording:', error);
      
      if (error.name === 'NotAllowedError') {
        setError('Microphone permission denied. Please allow microphone access and try again.');
      } else if (error.name === 'NotFoundError') {
        setError('No microphone found. Please connect a microphone and try again.');
      } else {
        setError(`Failed to start recording: ${error.message}`);
      }
      setIsRecording(false);
    }
  };

  const stopRecording = () => {
    setIsRecording(false);
    setShowWarning(false);
    
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      console.log('⏸️ Stopping MediaRecorder...');
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
    console.log('📝 submitLog called with text:', inputText);
    console.log('📋 Current mode:', mode);
    
    if (!inputText.trim()) {
      setError('No speech detected. Please try again.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      if (mode === 'quick') {
        console.log('⚡ Calling quickLog...');
        const response = await quickLog(inputText);
        console.log('✨ Got response:', response);
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
    // Just stop recording - the MediaRecorder onstop handler will transcribe and submit automatically
    stopRecording();
  };

  const handleTryAgain = () => {
    setError(null);
    setResult(null);
    setTranscript('');
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

  const switchInputMethod = (method) => {
    setInputMethod(method);
    setError(null);
    setTranscript('');
    setManualText('');
    setIsRecording(false);
    setIsTypeMode(false);
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
      {/* Input Method Toggle */}
      <div className="input-method-toggle">
        <button 
          className={inputMethod === 'voice' ? 'active' : ''}
          onClick={() => switchInputMethod('voice')}
        >
          🎤 Voice
        </button>
        <button 
          className={inputMethod === 'type' ? 'active' : ''}
          onClick={() => switchInputMethod('type')}
        >
          ⌨️ Type
        </button>
      </div>

      {/* Voice Mode */}
      {inputMethod === 'voice' && (
        <>
          {error && (
            <div className="error-message">
              <p>{error}</p>
              <div className="error-actions">
                <button onClick={handleTryAgain}>Try Again</button>
                <button onClick={() => switchInputMethod('type')}>Switch to Type</button>
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
          <p>Analyzing with AI... (this may take 30-60 seconds)</p>
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
        </>
      )}

      {/* Type Mode */}
      {inputMethod === 'type' && (
        <div className="type-mode-container">
          {error && (
            <div className="error-message">
              <p>{error}</p>
              <div className="error-actions">
                <button onClick={() => setError(null)}>Dismiss</button>
              </div>
            </div>
          )}

          {!isLoading && !error && (
            <div className="type-instructions">
              <p>
                {mode === 'quick' 
                  ? 'Type your symptoms. Be as detailed as you\'d like.'
                  : 'Type your symptoms. We\'ll ask follow-up questions after.'}
              </p>
            </div>
          )}

          {isLoading && (
            <div className="loading">
              <div className="spinner"></div>
              <p>Processing your log...</p>
            </div>
          )}

          {!isLoading && (
            <textarea
              className="text-input-area"
              value={manualText}
              onChange={(e) => setManualText(e.target.value)}
              placeholder="Example: I've had a headache since lunch, severity 7 out of 10, maybe from too much coffee"
              rows={6}
            />
          )}

          <div className="type-actions">
            <button 
              className="submit-button" 
              onClick={handleSubmitTyped}
              disabled={!manualText.trim() || isLoading}
            >
              Submit
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default VoiceRecorder;
