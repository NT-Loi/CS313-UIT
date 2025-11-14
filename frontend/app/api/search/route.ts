import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const query = searchParams.get("query")?.toLowerCase() || "";

  const dataDir = path.join(process.cwd(), "../data");
  const files = fs.readdirSync(dataDir);

  // Collect and filter papers
  const results = files
    .filter((file) => file.endsWith(".json"))
    .map((file) => {
      const content = JSON.parse(fs.readFileSync(path.join(dataDir, file), "utf8"));
      return {
        id: path.basename(file, ".json"),
        title: content.title || "Untitled Paper",
        abstract: content.abstract || "No abstract available.",
        ...content,
      };
    })
    .filter((paper) =>
      paper.title.toLowerCase().includes(query) ||
      paper.abstract.toLowerCase().includes(query)
    );

  return NextResponse.json(results);
}