import {
  FileArchive,
  FileAudio,
  File as FileIcon,
  FileImage,
  FileText,
  FileVideo,
} from "lucide-react";

// Helper function to get file icon
export const getFileIcon = (fileType: string) => {
  if (fileType.startsWith("image/"))
    return <FileImage className="h-6 w-6 text-blue-500" />;
  if (fileType.startsWith("audio/"))
    return <FileAudio className="h-6 w-6 text-purple-500" />;
  if (fileType.startsWith("video/"))
    return <FileVideo className="h-6 w-6 text-red-500" />;
  if (fileType.includes("pdf"))
    return <FileText className="h-6 w-6 text-red-500" />;
  if (fileType.includes("zip") || fileType.includes("archive"))
    return <FileArchive className="h-6 w-6 text-yellow-500" />;
  if (
    fileType.includes("spreadsheet") ||
    fileType.includes("csv") ||
    fileType.includes("xlsx")
  )
    return <FileText className="h-6 w-6 text-green-500" />;
  if (fileType.includes("presentation") || fileType.includes("ppt"))
    return <FileText className="h-6 w-6 text-orange-500" />;
  if (fileType.includes("document") || fileType.includes("doc"))
    return <FileText className="h-6 w-6 text-blue-500" />;
  return <FileIcon className="h-6 w-6 text-gray-500" />;
};
