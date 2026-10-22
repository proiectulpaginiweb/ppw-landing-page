# Proiectul Pagini Web

Responsive, buildless landing page for an AI-native company. Uses the supplied `ppw.png` brand asset and its yellow, green, and orange palette.

## Local preview

```sh
cd ~/projects/proiectul-pagini-web
npm run dev
```

Open http://127.0.0.1:4173. No npm dependencies or build step are required. Any static host can serve this directory.

## Content and interactions

- Romanian positioning, services, illustrative workflow, interactive journey, principles, FAQs, and contact section.
- Accessible keyboard-controlled journey tabs, mobile navigation, and native FAQ disclosure controls.
- Contact form submits to Web3Forms using the supplied public access key. Name, email, selected interest, and project details are combined into the message. Inline status feedback handles sending, success, and failure; failed submissions retain the visitor’s entries. All contact links point to the form; no recipient email address is displayed. Delivery goes to the recipient configured for the Web3Forms access key.
- Fonts are loaded from Google Fonts, with local system fallbacks. No analytics or tracking scripts.
- Service copy is proposed marketing copy; no customer logos, testimonials, or performance claims are invented.

Edit `index.html` for page content, `styles.css` for the design, and `script.js` for interactions. Journey panel copy is in `script.js`.
