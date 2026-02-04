import { extendTheme, type ThemeConfig } from '@chakra-ui/react';
import { mode } from '@chakra-ui/theme-tools';

const config: ThemeConfig = {
    initialColorMode: 'light',
    useSystemColorMode: false,
};

const colors = {
    brand: {
        50: '#e0f2ff',
        100: '#b8dbff',
        200: '#8ac4ff',
        300: '#5cadff',
        400: '#2e96ff',
        500: '#007fff',
        600: '#0066cc',
        700: '#004c99',
        800: '#003366',
        900: '#001933',
    },
    accent: {
        50: '#fdf2ff',
        100: '#f0d9ff',
        200: '#e3bfff',
        300: '#d6a6ff',
        400: '#c98cff',
        500: '#bd73ff',
        600: '#975ccc',
        700: '#714599',
        800: '#4c2e66',
        900: '#261733',
    },
    // Dark mode background alternatives
    dark: {
        bg: '#0f172a', // Slate 900
        card: '#1e293b', // Slate 800
        hover: '#334155', // Slate 700
    }
};

const fonts = {
    heading: "'Inter', sans-serif",
    body: "'Inter', sans-serif",
    mono: "'JetBrains Mono', monospace",
    writing: "'Merriweather', serif", // Special font for writing area
};

const components = {
    Button: {
        baseStyle: {
            fontWeight: '600',
            borderRadius: 'lg',
            transition: 'all 0.2s',
            _active: {
                transform: 'scale(0.98)',
            },
        },
        variants: {
            solid: (props: any) => ({
                bg: props.colorScheme === 'brand' ? 'brand.500' : undefined,
                _hover: {
                    bg: props.colorScheme === 'brand' ? 'brand.600' : undefined,
                    boxShadow: '0 4px 12px rgba(0, 127, 255, 0.3)',
                },
            }),
            ghost: (props: any) => ({
                _hover: {
                    bg: mode('gray.100', 'whiteAlpha.200')(props),
                },
            }),
            outline: {
                borderWidth: '2px',
            },
            // New premium variant
            premium: (props: any) => ({
                bg: 'transparent',
                border: '1px solid',
                borderColor: mode('gray.200', 'whiteAlpha.300')(props),
                color: mode('gray.700', 'white')(props),
                backdropFilter: 'blur(10px)',
                _hover: {
                    bg: mode('whiteAlpha.500', 'whiteAlpha.200')(props),
                    borderColor: 'brand.400',
                    boxShadow: '0 0 15px rgba(0, 127, 255, 0.15)',
                },
            }),
        },
        defaultProps: {
            colorScheme: 'brand',
        },
    },
    Card: {
        baseStyle: (props: any) => ({
            container: {
                bg: mode('white', 'dark.card')(props),
                borderRadius: 'xl',
                boxShadow: mode(
                    '0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03)',
                    '0 4px 6px -1px rgba(0, 0, 0, 0.2), 0 2px 4px -1px rgba(0, 0, 0, 0.1)'
                )(props),
                border: '1px solid',
                borderColor: mode('gray.100', 'whiteAlpha.100')(props),
                transition: 'all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1)',
                overflow: 'hidden',
                _hover: {
                    transform: 'translateY(-4px)',
                    boxShadow: mode(
                        '0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.04)',
                        '0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -2px rgba(0, 0, 0, 0.15)'
                    )(props),
                    borderColor: 'brand.200',
                },
            },
        }),
    },
    Input: {
        variants: {
            filled: (props: any) => ({
                field: {
                    bg: mode('gray.50', 'whiteAlpha.100')(props),
                    borderRadius: 'lg',
                    border: '1px solid',
                    borderColor: 'transparent',
                    _hover: {
                        bg: mode('gray.100', 'whiteAlpha.200')(props),
                    },
                    _focus: {
                        bg: 'transparent',
                        borderColor: 'brand.500',
                        boxShadow: '0 0 0 1px var(--chakra-colors-brand-500)',
                    },
                },
            }),
        },
        defaultProps: {
            variant: 'filled',
        },
    },
    Modal: {
        baseStyle: (props: any) => ({
            dialog: {
                bg: mode('white', 'dark.card')(props),
                borderRadius: '2xl',
                boxShadow: 'xl',
            },
            header: {
                fontFamily: 'heading',
                fontWeight: '700',
            },
        }),
    },
    Badge: {
        baseStyle: {
            borderRadius: 'full',
            px: 3,
            py: 1,
            textTransform: 'none',
            fontWeight: '600',
        },
        variants: {
            subtle: (props: any) => ({
                bg: itemColor(props.colorScheme, 'bg', props),
                color: itemColor(props.colorScheme, 'color', props),
            }),
        },
    },
};

// Helper for badge colors
function itemColor(scheme: string, type: 'bg' | 'color', props: any) {
    const isDark = props.colorMode === 'dark';
    // Simplified logic for demo
    if (type === 'bg') return isDark ? `${scheme}.900` : `${scheme}.100`;
    if (type === 'color') return isDark ? `${scheme}.200` : `${scheme}.700`;
    return undefined;
}

const styles = {
    global: (props: any) => ({
        body: {
            bg: mode('#f8fafc', 'dark.bg')(props), // Slate 50 or Slate 900
            color: mode('gray.800', 'gray.100')(props),
            fontFamily: 'body',
        },
        '::selection': {
            bg: 'brand.100',
            color: 'brand.900',
        },
    }),
};

const theme = extendTheme({
    config,
    colors,
    fonts,
    components,
    styles,
});

export default theme;
