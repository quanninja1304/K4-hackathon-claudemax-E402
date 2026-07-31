import React, { useState, useEffect, useRef } from "react";
import { useAppContext } from "../context/AppContext";
import { assets } from "../assets/assets";
import Message from "./Message";
import toast from "react-hot-toast";
import { PdfViewer } from "./PdfViewer";

const ChatBox = () => {

  const containerRef = useRef(null);

  const {
    user,
    selectedChat,
    theme,
    axios,
    token,
    updateChatMessages,
    currentDocId,
    highlightedText,
    highlightedPage,
    setHighlightedText,
    setHighlightedPage
  } = useAppContext();

  const [messages, setMessages] = useState([]);

  const [loading, setLoading] = useState(false);

  const [prompt, setPrompt] = useState('');

  const onSubmit = async (e) => {

    try {

      e.preventDefault();

      setLoading(true);

      const promptCopy = prompt;

      setPrompt('');

      const userMessage = {
        role: 'user',
        content: promptCopy,
        timestamp: Date.now()
      };

      setMessages(prev => [
        ...prev,
        userMessage
      ]);

      if (selectedChat) {
        updateChatMessages(
          selectedChat._id,
          userMessage
        );
      }

      // Call new Backend `/chat` API
      const { data } = await axios.post(
        'http://127.0.0.1:8000/chat',
        {
          message: promptCopy,
          doc_id: currentDocId,
          highlighted_text: highlightedText || null,
          highlighted_page: highlightedPage || null
        }
      );

      // Clear highlight state after sending
      setHighlightedText(null);
      setHighlightedPage(null);

      // data contains: { mode, answer, citations, security_flag, unverified_highlight, ... }
      if (data) {
        
        // Wrap response into a Message-compatible object
        const botMessage = {
          role: 'model',
          content: data.answer || data.llm_response?.answer || '',
          timestamp: Date.now(),
          mode: data.mode,
          citations: data.citations || [],
          security_flag: data.security_flag,
          unverified_highlight: data.unverified_highlight
        };

        setMessages(prev => [
          ...prev,
          botMessage
        ]);

        if (selectedChat) {
          updateChatMessages(
            selectedChat._id,
            botMessage
          );
        }

      } else {

        toast.error("Không nhận được phản hồi từ server");

      }

    } catch (error) {

      toast.error(
        error.response?.data?.message ||
        error.message
      );

    } finally {

      setLoading(false);

    }

  };

  useEffect(() => {

    if (selectedChat) {

      setMessages(
        selectedChat.messages || []
      );

    }

  }, [selectedChat]);

  useEffect(() => {

    if (containerRef.current) {

      containerRef.current.scrollTo({
        top: containerRef.current.scrollHeight,
        behavior: 'smooth',
      });

    }

  }, [messages]);

  return (
    <div className='flex w-full h-full'>
      
      {/* Left side: PDF Viewer */}
      <div className="hidden md:flex w-1/2 p-4 border-r border-gray-200 dark:border-gray-700 h-full">
        <PdfViewer />
      </div>

      {/* Right side: Chat */}
      <div className='flex-1 flex flex-col justify-between m-5 md:m-10 xl:mx-10 max-md:mt-14 h-[calc(100vh-80px)]'>

      {/* Chat Messages */}
      <div
        className='flex-1 mb-5 overflow-y-scroll scrollbar-thin
        scrollbar-thumb-purple-500/20'
        ref={containerRef}
      >

        {messages.length === 0 && (
          <div className='h-full flex flex-col justify-center items-center
          gap-2 text-primary'>

            <img
              src={theme === 'dark'
                ? assets.logo_full
                : assets.logo_full_dark
              }
              alt=""
              className='w-full max-w-56 sm:max-w-68'
            />

            <p className='mt-5 text-4xl sm:text-6xl sm:text-center
            text-gray-400 dark:text-white'>
              Enter your message to start the conversation.
            </p>

          </div>
        )}

        {messages.map((message, index) => (
          <Message key={index} message={message} />
        ))}

        {/* Loading */}
        {
          loading && (
            <div className='Loader flex items-center justify-center gap-1.5'>

              <div className='w-1.5 h-1.5 rounded-full bg-gray-500
              dark:bg-white animate-bounce'></div>

              <div className='w-1.5 h-1.5 rounded-full bg-gray-500
              dark:bg-white animate-bounce'></div>

              <div className='w-1.5 h-1.5 rounded-full bg-gray-500
              dark:bg-white animate-bounce'></div>

            </div>
          )
        }

      </div>

      {/* Highlight Indicator */}
      {highlightedText && (
        <div className="bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200 p-2 mb-2 rounded-md text-sm shadow-md relative">
          <span className="font-bold">Đang trích dẫn (Trang {highlightedPage || "?"}): </span>
          <span className="italic">"{highlightedText.substring(0, 50)}{highlightedText.length > 50 ? '...' : ''}"</span>
          <button 
            type="button"
            className="absolute top-1 right-2 text-yellow-600 dark:text-yellow-400 font-bold" 
            onClick={() => { setHighlightedText(null); setHighlightedPage(null); }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Prompt Input */}
      <form
        className='bg-primary/20 dark:bg-[#583C79]/30 border border-primary
        dark:border-[#80609F]/30 rounded-full w-full max-w-2xl p-3 pl-4
        mx-auto flex gap-4 items-center'
        onSubmit={onSubmit}
      >

        <input
          onChange={(e) => setPrompt(e.target.value)}
          value={prompt}
          type="text"
          placeholder="Type your messages here..."
          className="flex-1 w-full text-sm outline-none bg-transparent
          text-gray-700 dark:text-white
          placeholder-gray-400 dark:placeholder-gray-500"
          required
        />

        <button
          type="submit"
          disabled={loading}
        >

          <img
            className="w-8 cursor-pointer"
            src={loading
              ? assets.stop_icon
              : assets.send_icon
            }
            alt=""
          />

        </button>

      </form>
      </div>
    </div>
  );

};

export default ChatBox;