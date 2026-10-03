import { Access } from "@/components/access";
export const metadata = { title: "Acceder", robots: {index:false,follow:true} };
export default function Page() { return <Access intent="login" />; }
