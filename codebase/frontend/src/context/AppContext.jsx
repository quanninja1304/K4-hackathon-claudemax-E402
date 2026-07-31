import { createContext, useContext, useState, useEffect } from "react";
import axios from "axios";

axios.defaults.baseURL = import.meta.env.VITE_SERVER_URL;

const AppContext = createContext();

export const AppContextProvider = ({ children }) => {

    const [chats, setChats] = useState([]);
    const [selectedChat, setSelectedChat] = useState(null);

    const [theme, setTheme] = useState(
        localStorage.getItem("theme") || "light"
    );

    // --- Added for VLearn Dual-Engine Integration ---
    const [currentDocId, setCurrentDocId] = useState("d1-slide-hackathon.pdf"); // Default hardcoded for now
    const [highlightedText, setHighlightedText] = useState(null);
    const [highlightedPage, setHighlightedPage] = useState(null);

    // Theme
    useEffect(() => {

        if (theme === "dark") {
            document.documentElement.classList.add("dark");
        } else {
            document.documentElement.classList.remove("dark");
        }

        localStorage.setItem("theme", theme);

    }, [theme]);

    // Update local chat
    const updateChatMessages = (chatId, newMessage) => {

        setChats(prev =>
            prev.map(chat =>
                chat.id === chatId
                    ? {
                          ...chat,
                          messages: [...chat.messages, newMessage],
                      }
                    : chat
            )
        );

    };

    const value = {

        chats,
        setChats,

        selectedChat,
        setSelectedChat,

        theme,
        setTheme,

        updateChatMessages,

        axios,
        
        // --- Added for VLearn Dual-Engine Integration ---
        currentDocId,
        setCurrentDocId,
        highlightedText,
        setHighlightedText,
        highlightedPage,
        setHighlightedPage,

    };

    return (
        <AppContext.Provider value={value}>
            {children}
        </AppContext.Provider>
    );
};

export const useAppContext = () => useContext(AppContext);