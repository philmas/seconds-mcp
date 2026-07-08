from reflex.plugins.shared_tailwind import TailwindConfig
import reflex as rx

config = rx.Config(
    app_name="dashboard",
    # Backend on 8001 so it doesn't clash with the REST API on 8000.
    backend_port=8001,
    plugins=[
rx.plugins.TailwindV4Plugin(
            TailwindConfig(
                darkMode="class",
                plugins=["@tailwindcss/typography", "tailwind-scrollbar", "tailwindcss-animate"],
                theme={
                    "extend": {
                        "colors": {
                            "background": "var(--background)",
                            "foreground": "var(--foreground)",
                            "card": "var(--card)",
                            "card-foreground": "var(--card-foreground)",
                            "popover": "var(--popover)",
                            "popover-foreground": "var(--popover-foreground)",
                            "primary": "var(--primary)",
                            "primary-foreground": "var(--primary-foreground)",
                            "secondary": "var(--secondary)",
                            "secondary-foreground": "var(--secondary-foreground)",
                            "muted": "var(--muted)",
                            "muted-foreground": "var(--muted-foreground)",
                            "accent": "var(--accent)",
                            "accent-foreground": "var(--accent-foreground)",
                            "destructive": "var(--destructive)",
                            "border": "var(--border)",
                            "input": "var(--input)",
                            "ring": "var(--ring)",
                            "chart-1": "var(--chart-1)",
                            "chart-2": "var(--chart-2)",
                            "chart-3": "var(--chart-3)",
                            "chart-4": "var(--chart-4)",
                            "chart-5": "var(--chart-5)",
                            "sidebar": "var(--sidebar)",
                            "sidebar-foreground": "var(--sidebar-foreground)",
                            "sidebar-primary": "var(--sidebar-primary)",
                            "sidebar-primary-foreground": "var(--sidebar-primary-foreground)",
                            "sidebar-accent": "var(--sidebar-accent)",
                            "sidebar-accent-foreground": "var(--sidebar-accent-foreground)",
                            "sidebar-border": "var(--sidebar-border)",
                            "sidebar-ring": "var(--sidebar-ring)",
                        },
                        "fontFamily": {
                            "theme": "var(--font-family)",
                        },
                        "borderRadius": {
                            "sm": "var(--radius-sm)",
                            "md": "var(--radius-md)",
                            "lg": "var(--radius-lg)",
                            "xl": "var(--radius-xl)",
                            "2xl": "var(--radius-2xl)",
                            "3xl": "var(--radius-3xl)",
                            "4xl": "var(--radius-4xl)",
                        },
                        "padding": {
                            "card": "var(--card-padding)",
                        },
                        "gap": {
                            "card": "var(--card-gap)",
                        },
                        "boxShadow": {
                            "default": "var(--shadow)",
                        },
                    }
                },
            )
        ),
        rx.plugins.SitemapPlugin(),
        # Radix components (rx.heading, rx.hstack, ...) are used alongside
        # buridan/ui; enable the theme plugin explicitly to avoid the implicit-
        # enablement deprecation warning.
        rx.plugins.RadixThemesPlugin(),
    ]
)