import fs from "fs";
import path from "path";
import { PaperClientView } from "./paper-view";
import { Paper } from "@/lib/types";

// --- HÀM LẤY DỮ LIỆU ---
async function getPaperData(id: string): Promise<Paper | null> {
  if (!id || id === "undefined") {
    console.error("Lỗi ID is undefined.");
    return null;
  }

  try {
    const dataDir = path.join(process.cwd(), "data");
    const filePath = path.join(dataDir, `${id}.json`);

    if (!fs.existsSync(filePath)) {
      console.error(`File not found: ${filePath}`);
      return null;
    }

    const fileContent = fs.readFileSync(filePath, "utf8");
    const data = JSON.parse(fileContent);
    return data as Paper;
  } catch (error) {
    console.error(`Lỗi đọc file data cho ID: ${id}`, error);
    return null;
  }
}

interface PaperPageProps {
  params: Promise<{ id: string }>; // 👈 Next.js 15 yêu cầu Promise ở đây
}

export default async function PaperPage({ params }: PaperPageProps) {
  const { id: paperId } = await params; // 👈 await Promise để tránh warning
  const paper = await getPaperData(paperId);

  // PaperClientView là CLIENT COMPONENT => BackButton sẽ hoạt động
  return <PaperClientView paper={paper} />;
}
