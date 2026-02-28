import React, { useState, useRef, useEffect, useContext } from 'react';
import { RefreshContext } from '../context/RefreshContext';
import { quickLog, guidedLogStart, guidedLogRespond, guidedLogSave } from '../api/client';
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
  const [answers, setAnswers] = useState([]);
  
  const recognitionRef = useRef(null);
  const timerRef = useRef(null);
  const activeStreamRef = useRef(null);
  const retryCountRef = useRef(0);
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
        setError('No speech detected. Please try again.');
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
    setError(null);
    setResult(null);
    setTranscript('');
    setRecordingTime(0);
    setShowWarning(false);
    retryCountRef.current = 0; // Reset retry counter

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
        console.log('🎯 Starting guided log...');
        const response = await guidedLogStart(transcript);
        console.log('✨ Got guided response:', response);
        setGuidedState(response);
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
    if (!answer.trim()) {
      setError('Please provide an answer');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Send answer to backend and get next state
      const response = await guidedLogRespond(guidedState.session_id, answer);
      
      console.log('📝 Guided response:', response);
      
      // Check if conversation is complete
      if (response.is_complete) {
        // Save the extracted data to database
        const saveResponse = await guidedLogSave(response.extracted_data);
        setResult(saveResponse);
        setGuidedState(null);
        setAnswers([]);
        triggerRefresh(); // Refresh dashboard
      } else {
        // More questions to answer - update state
        setGuidedState(response);
        setAnswers([...answers, { question: guidedState.question, answer }]);
      }
    } catch (err) {
      console.error('Guided answer failed:', err);
      setError(err.message || 'Failed to process your answer. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setTranscript('');
    setResult(null);
    setError(null);
    setGuidedState(null);
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
    return (
      <div className="voice-recorder guided">
        {isLoading ? (
          <div className="loading">
            <div className="spinner"></div>
            <p>Processing your answer...</p>
          </div>
        ) : (
          <>
            {/* Show conversation history */}
            {answers.length > 0 && (
              <div className="conversation-history">
                {answers.map((qa, idx) => (
                  <div key={idx} className="conversation-item">
                    <div className="assistant-message">
                      <strong>Assistant:</strong> {qa.question}
                    </div>
                    <div className="user-message">
                      <strong>You:</strong> {qa.answer}
                    </div>
                  </div>
                ))}
              </div>
            )}
            
            {/* Current question */}
            <div className="current-question">
              <h3>{answers.length === 0 ? 'Follow-up' : `Question ${answers.length + 1}`}</h3>
              <p className="question">{guidedState.question}</p>
              
              {error && (
                <div className="error-message">
                  <p>{error}</p>
                </div>
              )}
              
              <input
                type="text"
                placeholder="Type your answer..."
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && e.target.value.trim()) {
                    handleGuidedAnswer(e.target.value.trim());
                    e.target.value = '';
                  }
                }}
                autoFocus
              />
              <p className="hint">Press Enter to submit</p>
            </div>
          </>
        )}
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
