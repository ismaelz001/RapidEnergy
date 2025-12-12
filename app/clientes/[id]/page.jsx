import { getCliente } from "@/lib/apiClient";
import ClienteDetailShell from "./ClienteDetailShell";

export const dynamic = "force-dynamic";

export default async function ClienteDetailPage({ params }) {
  const cliente = await getCliente(params.id);
  return <ClienteDetailShell initialCliente={cliente} />;
}
