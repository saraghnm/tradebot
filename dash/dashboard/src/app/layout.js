import "./globals.css";

export const metadata = {
  title: "zTrading Bot",
  description: "Live trading dashboard",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
