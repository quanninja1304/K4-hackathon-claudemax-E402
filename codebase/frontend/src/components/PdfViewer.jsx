import { useState, useRef, useEffect } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import { useAppContext } from "../context/AppContext";
import "react-pdf/dist/Page/TextLayer.css";
import "react-pdf/dist/Page/AnnotationLayer.css";

// Setup worker for react-pdf
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

export const PdfViewer = () => {
    const { currentDocId, setHighlightedText, setHighlightedPage } = useAppContext();
    const [numPages, setNumPages] = useState(null);
    const containerRef = useRef(null);

    function onDocumentLoadSuccess({ numPages }) {
        setNumPages(numPages);
    }

    const handleMouseUp = () => {
        const selection = window.getSelection();
        const text = selection.toString().trim();

        if (text) {
            setHighlightedText(text);

            // Try to find the page number from DOM
            let pageNum = null;
            let node = selection.anchorNode;
            
            // Traverse up to find the element with data-page-number attribute
            while (node && node !== document.body) {
                if (node.nodeType === Node.ELEMENT_NODE && node.hasAttribute('data-page-number')) {
                    pageNum = parseInt(node.getAttribute('data-page-number'), 10);
                    break;
                }
                node = node.parentNode;
            }

            setHighlightedPage(pageNum);
            console.log("Highlighted:", text, "on page:", pageNum);
        }
    };

    return (
        <div 
            ref={containerRef}
            className="w-full h-full overflow-y-auto bg-gray-100 dark:bg-gray-900 p-4 rounded-lg flex flex-col items-center"
            onMouseUp={handleMouseUp}
        >
            {currentDocId ? (
                <Document
                    file={`/${currentDocId}`} // assuming it's in public/
                    onLoadSuccess={onDocumentLoadSuccess}
                    className="flex flex-col gap-4"
                    loading={<div className="text-gray-500">Đang tải tài liệu...</div>}
                    error={<div className="text-red-500">Không thể tải tài liệu. Vui lòng đảm bảo file tồn tại ở public/{currentDocId}</div>}
                >
                    {Array.from(new Array(numPages), (el, index) => (
                        <div key={`page_${index + 1}`} id={`pdf-page-${index + 1}`} className="shadow-lg rounded-md overflow-hidden bg-white mb-4">
                            <Page 
                                pageNumber={index + 1} 
                                renderTextLayer={true} 
                                renderAnnotationLayer={true}
                                width={600}
                            />
                        </div>
                    ))}
                </Document>
            ) : (
                <div className="text-gray-500 flex items-center justify-center h-full">
                    Chưa chọn tài liệu nào.
                </div>
            )}
        </div>
    );
};
