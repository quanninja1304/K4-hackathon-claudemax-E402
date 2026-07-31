import React, { useEffect } from "react";
import { assets } from "../assets/assets";
import moment from "moment";
import Markdown from "react-markdown";
import Prism from "prismjs";

const Message = ({ message }) => {

  useEffect(() => {
    Prism.highlightAll();
  }, [message.content]);

  return (
    <div>
      {message.role === 'user' ? (
        <div className='flex items-start justify-end my-4 gap-2 w-full'>

          <div className='flex flex-col gap-2 p-2 px-4 bg-slate-50
          dark:bg-[#57317C]/30 border border-[#80609F]/30 rounded-md
          max-w-2xl shadow-sm'>

            <p className='text-sm text-gray-700 dark:text-primary'>
              {message.content}
            </p>
  
            <span className='text-xs text-gray-400 dark:text-[#B1A6C0]'>
              {moment(message.timestamp).fromNow()}
            </span>

          </div>

          <img
            className='w-8 h-8 rounded-full object-cover'
            src={assets.user_icon}
            alt=""
          />
        </div>
      ) : (
        <div className='flex justify-start w-full'>

          {(() => {
            let borderClass = 'border-[#80609F]/30';
            let badge = null;
            if (message.security_flag) {
              borderClass = 'border-red-500 shadow-[0_0_10px_rgba(239,68,68,0.5)] border-2';
              badge = <span className="inline-block bg-red-500 text-white text-xs px-2 py-1 rounded-md mb-2">Cảnh báo An Toàn</span>;
            } else if (message.unverified_highlight) {
              borderClass = 'border-yellow-500 shadow-[0_0_10px_rgba(234,179,8,0.5)] border-2';
              badge = <span className="inline-block bg-yellow-500 text-white text-xs px-2 py-1 rounded-md mb-2">Đoạn bôi đen không xác định</span>;
            } else if (message.mode === 'anchored_ambiguous') {
              borderClass = 'border-orange-500 shadow-[0_0_10px_rgba(249,115,22,0.5)] border-2';
              badge = <span className="inline-block bg-orange-500 text-white text-xs px-2 py-1 rounded-md mb-2">Trích dẫn đa trang (Dự đoán)</span>;
            }

            return (
              <div className={`inline-flex flex-col gap-2 p-2 px-4 max-w-2xl
              bg-primary/20 dark:bg-[#57317C]/30 rounded-md my-4 ${borderClass}`}>

                {badge}

                {message.isImage ? (
                  <img
                    src={message.content}
                    alt=""
                    className="rounded-md max-w-full"
                  />
                ) : (
                  <div className='text-sm text-gray-700 dark:text-primary reset-tw'>
                    <Markdown>{message.content}</Markdown>
                  </div>
                )}

                {/* Citations UI */}
                {message.citations && message.citations.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-2 border-t border-gray-300 dark:border-gray-600 pt-2">
                    {message.citations.map((c, idx) => {
                      const isCurrentDoc = c.doc_id === 'd1-slide-hackathon.pdf'; // Hardcoded for now, could get from context
                      return (
                        <button 
                          key={idx} 
                          className={`text-xs px-2 py-1 rounded-full border cursor-pointer hover:opacity-80 transition-opacity ${isCurrentDoc ? 'bg-blue-100 text-blue-800 border-blue-300 dark:bg-blue-900 dark:text-blue-200 dark:border-blue-700' : 'bg-gray-200 text-gray-800 border-gray-300 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600'}`}
                        >
                          {isCurrentDoc ? `Trang ${c.page}` : `[${c.doc_id}] Trang ${c.page}`}
                        </button>
                      );
                    })}
                  </div>
                )}

                <span className='text-xs text-gray-400 dark:text-[#B1A6C0] mt-1'>
                  {moment(message.timestamp).fromNow()}
                </span>

              </div>
            );
          })()}

        </div>
      )}
    </div>
  );
};

export default Message;