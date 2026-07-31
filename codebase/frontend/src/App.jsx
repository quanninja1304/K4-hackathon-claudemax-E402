import React from "react";
import { Routes, Route, useLocation } from "react-router-dom";
import ChatBox from "./components/ChatBox";
import Support from "./pages/support";
import KnowledgeBase from "./pages/knowledge-base";
import Loading from "./pages/Loading";
import { assets } from "./assets/assets";
import "./assets/prism.css";
import { Toaster } from "react-hot-toast";

const App = () => {
  const { pathname } = useLocation();

  if (pathname === "/loading") {
    return <Loading />;
  }

  return (
    <>
      <Toaster />

      <div className="dark:bg-gradient-to-b from-[#242124] to-[#000000] dark:text-white">
        <div className="flex h-screen w-screen overflow-hidden">

          <Routes>
            <Route path="/" element={<ChatBox />} />
            <Route path="/knowledge-base" element={<KnowledgeBase />} />
            <Route path="/support" element={<Support />} />
            <Route path="/loading" element={<Loading />} />
          </Routes>
        </div>
      </div>
    </>
  );
};

export default App;