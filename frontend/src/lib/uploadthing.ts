import { generateReactHelpers } from "@uploadthing/react";

// eslint-disable-next-line boundaries/dependencies -- OurFileRouter type is needed here for type-safe helpers; shared→app boundary is unavoidable for this UploadThing pattern
import type { OurFileRouter } from "@/app/api/uploadthing/core";

export const { uploadFiles, useUploadThing } =
  generateReactHelpers<OurFileRouter>();
