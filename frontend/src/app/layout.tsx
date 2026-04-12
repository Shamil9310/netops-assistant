// root layout with dark theme

export default function RootLayout({ children }) {
    return (
        <html lang="en">
            <body className="dark-theme">
                {children}
            </body>
        </html>
    );
}