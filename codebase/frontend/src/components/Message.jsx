import React, { useEffect } from "react";
import { assets } from "../assets/assets";
import moment from "moment";
import Markdown from "react-markdown";
import Prism from "prismjs";
import toast from "react-hot-toast";

const CustomLink = ({ href, children }) => {
  return (
    <span className="relative group inline-block">
      <a href={href} target="_blank" rel="noopener noreferrer" className="text-blue-600 dark:text-blue-400 font-medium hover:underline decoration-blue-400 underline-offset-2">
        {children}
      </a>
      {/* Tooltip / Hover Card */}
      <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 hidden group-hover:flex flex-col w-64 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 shadow-xl rounded-lg p-3 z-50">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-bold text-gray-800 dark:text-gray-200 truncate flex-1">{href}</span>
          <span className="text-[10px] bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-300 px-1.5 py-0.5 rounded">External</span>
        </div>
        <p className="text-[11px] text-gray-500 dark:text-gray-400 leading-tight">
          Click để mở liên kết ở Tab mới.
        </p>
        {/* Arrow */}
        <div className="absolute left-1/2 -translate-x-1/2 top-full w-0 h-0 border-l-[6px] border-r-[6px] border-t-[6px] border-l-transparent border-r-transparent border-t-white dark:border-t-gray-800 filter drop-shadow-[0_1px_1px_rgba(0,0,0,0.1)]"></div>
      </div>
    </span>
  );
};

const Message = ({ message, onFollowUpClick }) => {

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
                    <Markdown components={{ a: CustomLink }}>
                      {message.content.replace(/(?<!\]\()(https?:\/\/[^\s\)]+)/g, '[$1]($1)')}
                    </Markdown>
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
                          onClick={() => {
                            if (isCurrentDoc) {
                              const el = document.getElementById(`pdf-page-${c.page}`);
                              if (el) {
                                el.scrollIntoView({ behavior: 'smooth', block: 'start' });
                              } else {
                                toast.error(`Trang ${c.page} chưa được load.`);
                              }
                            } else {
                              toast.error(`Nội dung này nằm ở tài liệu khác: ${c.doc_id}`);
                            }
                          }}
                          className={`text-xs px-2 py-1 rounded-full border cursor-pointer hover:opacity-80 transition-opacity ${isCurrentDoc ? 'bg-blue-100 text-blue-800 border-blue-300 dark:bg-blue-900 dark:text-blue-200 dark:border-blue-700' : 'bg-gray-200 text-gray-800 border-gray-300 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600'}`}
                        >
                          {isCurrentDoc ? `Trang ${c.page}` : `[${c.doc_id}] Trang ${c.page}`}
                        </button>
                      );
                    })}
                  </div>
                )}

                {/* Follow-up Questions UI */}
                {message.follow_up && message.follow_up.length > 0 && (
                  <div className="mt-3 flex flex-col gap-2 border-t border-gray-300 dark:border-gray-600 pt-3">
                    <p className="text-xs font-semibold text-gray-500 dark:text-gray-400">Câu hỏi gợi ý:</p>
                    <div className="flex flex-wrap gap-2">
                      {message.follow_up.map((q, idx) => (
                        <button 
                          key={idx} 
                          onClick={() => onFollowUpClick && onFollowUpClick(q)}
                          className="text-xs px-3 py-1.5 rounded-md bg-purple-100 text-purple-800 hover:bg-purple-200 border border-purple-300 dark:bg-purple-900/40 dark:text-purple-200 dark:border-purple-700/50 dark:hover:bg-purple-800/60 text-left transition-colors"
                        >
                          {q}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* External Links UI (Google Search) */}
                {message.external_links && message.external_links.length > 0 && (
                  <div className="mt-3 flex flex-col gap-2 border-t border-gray-300 dark:border-gray-600 pt-3">
                    <p className="text-xs font-semibold text-gray-500 dark:text-gray-400">Tài liệu đọc thêm (Tìm kiếm Web):</p>
                    <div className="flex flex-wrap gap-2">
                      {message.external_links.map((link, idx) => (
                        <a 
                          key={idx} 
                          href={link.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="group relative flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-md bg-blue-50 text-blue-800 hover:bg-blue-100 border border-blue-200 dark:bg-blue-900/40 dark:text-blue-200 dark:border-blue-700/50 dark:hover:bg-blue-800/60 transition-colors"
                        >
                          <span className="font-bold">🌍 {link.type}</span>
                          <span className="truncate max-w-[150px]">{link.title || link.domain}</span>
                          
                          {/* Rich Tooltip (Hover Card) */}
                          <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 hidden group-hover:flex flex-col w-64 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 shadow-xl rounded-lg p-3 z-50">
                            <p className="text-xs font-bold text-gray-800 dark:text-gray-200 mb-1 line-clamp-2">{link.title}</p>
                            <p className="text-[10px] text-gray-500 truncate mb-1">{link.url}</p>
                            {link.snippet && <p className="text-[11px] text-gray-600 dark:text-gray-400 line-clamp-3">{link.snippet}</p>}
                            {/* Arrow */}
                            <div className="absolute left-1/2 -translate-x-1/2 top-full w-0 h-0 border-l-[6px] border-r-[6px] border-t-[6px] border-l-transparent border-r-transparent border-t-white dark:border-t-gray-800 filter drop-shadow-[0_1px_1px_rgba(0,0,0,0.1)]"></div>
                          </div>
                        </a>
                      ))}
                    </div>
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