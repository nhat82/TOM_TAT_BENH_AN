/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
  	extend: {
  		colors: {
  			primary: '#2f6fed',
  			'primary-foreground': '#ffffff',
  			'on-primary': '#ffffff',
  			'primary-container': '#eef4fe',
  			'on-primary-container': '#16263d',
  			secondary: '#0d9488',
  			'secondary-foreground': '#ffffff',
  			'on-secondary': '#ffffff',
  			'secondary-container': '#cdf5f0',
  			'on-secondary-container': '#0f5044',
  			background: '#f5f8fc',
  			'on-background': '#16263d',
  			surface: '#f5f8fc',
  			'surface-bright': '#ffffff',
  			'surface-dim': '#e4eaf2',
  			'surface-variant': '#eef4fe',
  			'surface-container': '#f1f5fb',
  			'surface-container-low': '#f5f8fc',
  			'surface-container-high': '#e9eff8',
  			'surface-container-highest': '#e4eaf2',
  			'surface-container-lowest': '#ffffff',
  			outline: '#c5d1dc',
  			'outline-variant': '#e4eaf2',
  			'on-surface': '#16263d',
  			'on-surface-variant': '#8696ab',
  			error: '#dc2626',
  			'on-error': '#ffffff',
  			'error-container': '#fef2f2',
  			'on-error-container': '#7f1d1d',
  			foreground: 'hsl(var(--foreground))',
  			card: {
  				DEFAULT: 'hsl(var(--card))',
  				foreground: 'hsl(var(--card-foreground))'
  			},
  			popover: {
  				DEFAULT: 'hsl(var(--popover))',
  				foreground: 'hsl(var(--popover-foreground))'
  			},
  			muted: {
  				DEFAULT: 'hsl(var(--muted))',
  				foreground: 'hsl(var(--muted-foreground))'
  			},
  			accent: {
  				DEFAULT: 'hsl(var(--accent))',
  				foreground: 'hsl(var(--accent-foreground))'
  			},
  			destructive: {
  				DEFAULT: 'hsl(var(--destructive))',
  				foreground: 'hsl(var(--destructive-foreground))'
  			},
  			border: 'hsl(var(--border))',
  			input: 'hsl(var(--input))',
  			ring: 'hsl(var(--ring))',
  			chart: {
  				'1': 'hsl(var(--chart-1))',
  				'2': 'hsl(var(--chart-2))',
  				'3': 'hsl(var(--chart-3))',
  				'4': 'hsl(var(--chart-4))',
  				'5': 'hsl(var(--chart-5))'
  			},
  			sidebar: {
  				DEFAULT: 'hsl(var(--sidebar))',
  				foreground: 'hsl(var(--sidebar-foreground))',
  				primary: 'hsl(var(--sidebar-primary))',
  				'primary-foreground': 'hsl(var(--sidebar-primary-foreground))',
  				accent: 'hsl(var(--sidebar-accent))',
  				'accent-foreground': 'hsl(var(--sidebar-accent-foreground))',
  				border: 'hsl(var(--sidebar-border))',
  				ring: 'hsl(var(--sidebar-ring))'
  			}
  		},
  		borderRadius: {
  			DEFAULT: '0.25rem',
  			sm: 'calc(var(--radius) - 4px)',
  			lg: 'var(--radius)',
  			xl: '0.875rem',
  			'2xl': '0.875rem',
  			full: '9999px',
  			md: 'calc(var(--radius) - 2px)'
  		},
  		spacing: {
  			md: '16px',
  			gutter: '32px',
  			lg: '24px',
  			xs: '4px',
  			xl: '48px',
  			sm: '8px',
  			unit: '4px'
  		},
  		fontFamily: {
  			sans: [
  				'Be Vietnam Pro',
  				'IBM Plex Sans',
  				'Inter',
  				'system-ui',
  				'sans-serif'
  			]
  		},
  		fontSize: {
  			'title-sm': [
  				'16px',
  				{
  					lineHeight: '1.5',
  					fontWeight: '600'
  				}
  			],
  			'headline-lg': [
  				'26px',
  				{
  					lineHeight: '1.25',
  					letterSpacing: '-0.02em',
  					fontWeight: '700'
  				}
  			],
  			'headline-md': [
  				'20px',
  				{
  					lineHeight: '1.4',
  					letterSpacing: '-0.01em',
  					fontWeight: '600'
  				}
  			],
  			'headline-sm': [
  				'17px',
  				{
  					lineHeight: '1.4',
  					letterSpacing: '-0.01em',
  					fontWeight: '600'
  				}
  			],
  			'body-md': [
  				'15px',
  				{
  					lineHeight: '1.6',
  					fontWeight: '400'
  				}
  			],
  			'body-sm': [
  				'13px',
  				{
  					lineHeight: '1.5',
  					fontWeight: '400'
  				}
  			],
  			'label-caps': [
  				'11px',
  				{
  					lineHeight: '1',
  					letterSpacing: '0.05em',
  					fontWeight: '600'
  				}
  			],
  			'data-mono': [
  				'14px',
  				{
  					lineHeight: '1.4',
  					fontWeight: '500'
  				}
  			],
  			'display-lg': [
  				'28px',
  				{
  					lineHeight: '1.2',
  					letterSpacing: '-0.02em',
  					fontWeight: '700'
  				}
  			]
  		},
  		maxWidth: {
  			'container-max': '1320px'
  		},
  		boxShadow: {
  			card: '0 1px 2px rgba(20,40,80,.04), 0 6px 20px rgba(20,40,80,.05)'
  		}
  	}
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/container-queries'),
      require("tailwindcss-animate")
],
}
