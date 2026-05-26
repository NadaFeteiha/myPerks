import { createUploadthing, type FileRouter } from "uploadthing/next";

const f = createUploadthing();

export const ourFileRouter = {
    pdfUploader: f({ pdf: { maxFileSize: "16MB", maxFileCount: 1 } })
        .middleware(async () => {
            return {};
        })
        .onUploadComplete(async ({ file }) => {
            console.log("Upload complete:", file.url);
        }),
} satisfies FileRouter;

export type OurFileRouter = typeof ourFileRouter;
