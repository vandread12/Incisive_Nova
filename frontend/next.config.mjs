/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Output standalone para imágenes Docker slim (copia sólo lo necesario).
  output: "standalone",
  env: {
    NEXT_PUBLIC_APP_NAME: "Incisive Nova",
    NEXT_PUBLIC_PROJECT_ID: "incisive-nova",
  },
};

export default nextConfig;
