import { useFilePublicUrl } from "@vbkg/api-client";
import { Button } from "@vbkg/ui";

interface DownloadFileButtonProps {
  file_id: string;
}

export default function DownloadFileButton({
  file_id,
}: DownloadFileButtonProps) {
  const { data: fileUrl } = useFilePublicUrl({
    id: file_id,
  });

  const { data: url } = fileUrl || {};

  if (!url) {
    return <Button disabled>Tải xuống</Button>;
  }

  const handleDownload = () => {
    const link = document.createElement("a");
    link.href = url;
    link.download = file_id; // Set the desired filename here
    link.target = "_blank"; // Open in a new tab
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return <Button onClick={() => handleDownload()}>Tải xuống</Button>;
}
