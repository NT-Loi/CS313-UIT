// app/api/search/route.ts
import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const query = searchParams.get("query")?.toLowerCase() || "";

  const dataDir = path.join(process.cwd(), "data");
  if (!fs.existsSync(dataDir)) {
    return NextResponse.json([], { status: 200 });
  }

  const files = fs.readdirSync(dataDir);

  const results = files
    .filter((file) => file.endsWith(".json"))
    .map((file) => {
      const filePath = path.join(dataDir, file);
      const content = JSON.parse(fs.readFileSync(filePath, "utf8"));
      const id = path.basename(file, ".json");

      return {
        id,
        title: content.title || "Untitled Paper",
        abstract: content.abstract || "No abstract available.",
        pdf_url: content.pdf_url || null,
        citations_by_year: content.citations_by_year || {},
        ...content,
      };
    })
    .filter((paper) =>
      paper.title.toLowerCase().includes(query) ||
      (paper.abstract && paper.abstract.toLowerCase().includes(query))
    );

  return NextResponse.json(results);
}