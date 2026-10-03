import { Access } from "@/components/access";
export const metadata = { title: "Crear cuenta", robots: {index:false,follow:true} };
export default function Page() { return <Access intent="signup" />; }
