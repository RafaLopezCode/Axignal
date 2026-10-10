import "@/components/subscriber-portfolio.css";
import "@/components/observatory.css";
import { SubscriberPortfolioExperience } from "@/components/subscriber-portfolio";
export const metadata = { title: "Tu cartera", robots: { index: false, follow: false } };
export default function AccountPage() { return <SubscriberPortfolioExperience/>; }
