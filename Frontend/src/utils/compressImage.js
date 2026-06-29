const MAX_OUTPUT_CHARS = 120_000; // ~90KB JPEG — safe for JSON request limits

function isImageFile(file) {
  if (file.type?.startsWith("image/")) return true;
  return /\.(png|jpe?g|gif|webp|bmp)$/i.test(file.name || "");
}

function loadImageFromFile(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const img = new Image();
      img.onload = () => resolve(img);
      img.onerror = () => reject(new Error("Invalid image file"));
      img.src = reader.result;
    };
    reader.onerror = () => reject(new Error("Failed to read image"));
    reader.readAsDataURL(file);
  });
}

function renderToDataUrl(img, maxDimension, quality) {
  const scale = Math.min(1, maxDimension / Math.max(img.width, img.height));
  const width = Math.max(1, Math.round(img.width * scale));
  const height = Math.max(1, Math.round(img.height * scale));
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, width, height);
  ctx.drawImage(img, 0, 0, width, height);
  return canvas.toDataURL("image/jpeg", quality);
}

/**
 * Resize and compress an image file to a JPEG data URL suitable for profile storage.
 */
export async function compressImage(file) {
  if (!isImageFile(file)) {
    throw new Error("Unsupported image type");
  }

  const img = await loadImageFromFile(file);

  let maxDimension = 400;
  let quality = 0.82;
  let dataUrl = renderToDataUrl(img, maxDimension, quality);

  while (dataUrl.length > MAX_OUTPUT_CHARS && (quality > 0.45 || maxDimension > 200)) {
    if (quality > 0.45) {
      quality -= 0.1;
    } else {
      maxDimension = Math.round(maxDimension * 0.85);
      quality = 0.75;
    }
    dataUrl = renderToDataUrl(img, maxDimension, quality);
  }

  if (dataUrl.length > MAX_OUTPUT_CHARS) {
    throw new Error("Image is too large even after compression");
  }

  return dataUrl;
}

export { isImageFile };
