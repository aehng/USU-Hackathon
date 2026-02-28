import React, { useState, useRef, useEffect, useContext } from 'react';
import { RefreshContext } from '../context/RefreshContext';
import { quickLog, guidedLogStart, guidedLogRespond, guidedLogFinalize, transcribeAudio } from '../api/client';
import './VoiceRecorder.css';

function VoiceRecorder({ mode, onLogSaved }) {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [manualText, setManualText] = useState('');
  const [inputMethod, setInputMethod] = useState('voice'); // 'voice' or 'type'
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [recordingTime, setRecordingTime] = useState(0);
  
  // Guided mode state
  const [guidedState, setGuidedState] = useState(null);
  const [answers, setAnswers] = useState([]);
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerRef = useRef(null);
  const activeStreamRef = useRef(null);
  const { triggerRefresh } = useContext(RefreshContext);

  // Recording timer
  useEffect(() => {
    if (isRecording) {
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [isRecording]);

  const startRecording = async () => {
    setError(null);
    setResult(null);
    setTranscript('');
    setRecordingTime(0);
    audioChunksRef.current = [];

    try {
      console.log('🎤 Requesting microphone access...');
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      activeStreamRef.current = stream;
      
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorder.onstop = async () => {
        console.log('📼 Recording stopped, processing audio...');
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        console.log('📦 Audio blob size:', audioBlob.size);
        
        if (audioBlob.size < 100) {
          setError('Recording too short. Please try again.');
          return;
        }
        
        // Transcribe the audio
        setIsLoading(true);
        try {
          console.log('🔄 Sending to Whisper for transcription...');
          const { text } = await transcribeAudio(audioBlob);
          console.log('✅ Transcription:', text);
          setTranscript(text);
          
          // Auto-submit the transcription
          await submitLog(text);
        } catch (err) {
          console.error('Transcription error:', err);
          setError(err.message || 'Failed to transcribe audio. Please try again.');
        } finally {
          setIsLoading(false);
        }
      };
      
      mediaRecorder.start();
      setIsRecording(true);
      console.log('✅ Recording started');
      
    } catch (e) {
      console.error('Failed to start recording:', e);
      if (e.name === 'NotAllowedError') {
        setError('Microphone permission denied. Please allow microphone access and try again.');
      } else if (e.name === 'NotFoundError') {
        setError('No microphone found. Please connect a microphone and try again.');
      } else {
        setError(e.message || 'Failed to start recording. Please try again.');
      }
    }
  };

  const stopRecording = () => {
    setIsRecording(false);
    
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
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
    
    if (!inputText || !inputText.trim()) {
      setError('No text to submit. Please try again.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      if (mode === 'quick') {
        console.log('⚡ Calling quickLog...');
        const response = await quickLog(inputText);
        console.log('✅ Got response:', response);
        setResult(response);
        triggerRefresh(); // This handles context/history
        if (onLogSaved) onLogSaved(); // <-- ADD THIS to refresh the dashboard charts
      } else {
        // Guided mode
        console.log('🎯 Starting guided log...');
        const response = await guidedLogStart(inputText);
        console.log('✅ Got guided response:', response);
        
        if (response.is_complete) {
          // Conversation complete immediately - finalize to get structured data
          try {
            const extractedData = await guidedLogFinalize(response.session_id);
            setResult({
              status: 'success',
              message: 'Guided log completed',
              extracted_data: extractedData
            });
          } catch (finalizeError) {
            // If finalize fails, we still show success since data was saved to DB
            console.error('Finalize error (data likely saved):', finalizeError);
            setResult({
              status: 'success',
              message: 'Log saved successfully! Check dashboard for details.'
            });
          }
          triggerRefresh();
          if (onLogSaved) onLogSaved(); // <-- ADD THIS to refresh the dashboard charts
        } else {
          // More questions needed
          setGuidedState(response);
          setAnswers([]);
        }
      }
    } catch (err) {
      console.error('Log failed:', err);
      setError(err.message || 'Failed to process your log. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGuidedAnswer = async (answer) => {
    if (!answer.trim()) {
      setError('Please provide an answer');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await guidedLogRespond(guidedState.session_id, answer);
      
      console.log('📝 Guided response:', response);
      
// Inside handleGuidedAnswer
if (response.is_complete) {
  try {
    const data = await guidedLogFinalize(response.session_id);
    
    setResult({
      status: 'success',
      ...data // Spread the data directly since client.js already unwrapped it
    });
  } catch (finalizeError) {
    // If finalize fails, we still show success since data was saved to DB
    console.error('Finalize error (data likely saved):', finalizeError);
    setResult({
      status: 'success',
      message: 'Log saved successfully! Check dashboard for details.'
    });
  }
  
  setGuidedState(null);
  setAnswers([]);
  triggerRefresh();
  if (onLogSaved) onLogSaved();
} else {
        // More questions - update state
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
    setManualText('');
    setResult(null);
    setError(null);
    setGuidedState(null);
    setAnswers([]);
  };

  const switchInputMethod = (method) => {
    setInputMethod(method);
    setError(null);
    setTranscript('');
    setManualText('');
  };

  const handleSubmitTyped = async () => {
    await submitLog(manualText);
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
                <button onClick={() => setError(null)}>Dismiss</button>
              </div>
            </div>
          )}

          {!isRecording && !isLoading && !error && (
            <div className="recorder-idle">
              <p className="instructions">
                {mode === 'quick' 
                  ? 'Tap the mic to record your symptoms. Audio will be transcribed using Whisper.'
                  : 'Tap the mic to record. We\'ll transcribe and ask follow-up questions.'}
              </p>
            </div>
          )}

          {isRecording && (
            <div className="recorder-active">
              <div className="recording-indicator">
                <span className="pulse"></span>
                Recording... {recordingTime}s
              </div>
              <p className="recording-hint">Speak clearly about your symptoms</p>
            </div>
          )}

          {isLoading && (
            <div className="loading">
              <div className="spinner"></div>
              <p>Transcribing with Whisper and analyzing...</p>
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
                onClick={stopRecording}
              >
                Stop & Submit
              </button>
            )}
          </div>
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

          {!isLoading && (
            <>
              <div className="type-instructions">
                <p>
                  {mode === 'quick' 
                    ? 'Type your symptoms. Be as detailed as you\'d like.'
                    : 'Type your symptoms. We\'ll ask follow-up questions after.'}
                </p>
              </div>

              <textarea
                className="text-input-area"
                value={manualText}
                onChange={(e) => setManualText(e.target.value)}
                placeholder="Example: I've had a headache since lunch, severity 7 out of 10, maybe from too much coffee"
                rows={6}
              />

              <div className="type-actions">
                <button 
                  className="submit-button" 
                  onClick={handleSubmitTyped}
                  disabled={!manualText.trim()}
                >
                  Submit
                </button>
              </div>
            </>
          )}

          {isLoading && (
            <div className="loading">
              <div className="spinner"></div>
              <p>Processing your log...</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default VoiceRecorder;
