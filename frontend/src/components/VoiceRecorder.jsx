import React, { useState, useRef, useEffect, useContext } from 'react';
import { RefreshContext } from '../context/RefreshContext';
import { quickLog, guidedLogStart, guidedLogFinalize } from '../api/client';
import './VoiceRecorder.css';

function VoiceRecorder({ mode }) {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState('');
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
  const { triggerRefresh } = useContext(RefreshContext);

  // Initialize Web Speech API
  useEffect(() => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      setError('Web Speech API is not supported in this browser. Please use Chrome or Edge.');
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onresult = (event) => {
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
      console.error('Speech recognition error:', event.error);
      if (event.error === 'no-speech') {
        setError('No speech detected. Please try again.');
      } else if (event.error === 'not-allowed') {
        setError('Microphone access denied. Please allow microphone access.');
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
    if (!window.isSecureContext) {
      throw new Error('Microphone access requires HTTPS or localhost. Open the app as https://... or http://localhost:5173.');
    }

    if (!navigator.mediaDevices?.getUserMedia) {
      throw new Error('Microphone API is unavailable in this browser context. Please use Chrome or Edge.');
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      activeStreamRef.current = stream;
    } catch (error) {
      if (error.name === 'NotAllowedError' || error.name === 'SecurityError') {
        throw new Error('Microphone permission is blocked. In Edge: click the lock icon in the address bar -> Site permissions -> Microphone -> Allow, then try again.');
      }

      if (error.name === 'NotFoundError') {
        throw new Error('No microphone was found on this device.');
      }

      throw new Error('Could not access microphone. Please check browser permissions and try again.');
    }
  };

  const startRecording = async () => {
    setError(null);
    setResult(null);
    setTranscript('');
    setRecordingTime(0);
    setShowWarning(false);

    try {
      await ensureMicrophonePermission();
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

  const handleStopAndSubmit = async () => {
    stopRecording();

    if (!transcript.trim()) {
      setError('No speech detected. Please try again.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      if (mode === 'quick') {
        const response = await quickLog(transcript);
        setResult(response);
        triggerRefresh(); // Trigger refresh for dashboard/history
      } else {
        // Guided mode
        const response = await guidedLogStart(transcript);
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
    // TODO: Show manual form
    alert('Manual form not implemented yet');
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

      <div className="controls">
        {!isRecording && !isLoading && (
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

      {transcript && !isRecording && !isLoading && !error && (
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
