// "use client";

// import {
//   Bar,
//   BarChart,
//   CartesianGrid,
//   Legend,
//   ResponsiveContainer,
//   Tooltip,
//   XAxis,
//   YAxis,
// } from "recharts";
// import Card from "./Card";
// import { useApi } from "@/lib/useApi";
// import type { Results } from "@/lib/types";

// export default function ModelsTab({ dataset }: { dataset: string }) {
//   const { data, error } = useApi<Results>("/models/results?dataset=" + dataset);
//   if (error) return <p className="text-sm text-brand">{error}</p>;
//   if (!data) return <p className="text-sm text-muted">Loading…</p>;

//   const chart = data.models.map((m) => ({
//     name: m.name,
//     Accuracy: m.final.accuracy,
//     Recall: m.final.recall,
//     F1: m.final.f1,
//   }));
//   const best = data.models.find((m) => m.name === data.best_model)!;

//   return (
//     <div className="space-y-6">
//       <Card
//         title={`Test scores (trained on ${(data.base_rows + data.stream_rows).toLocaleString()} rows, tested on ${data.test_rows.toLocaleString()})`}
//       >
//         <div className="overflow-x-auto">
//           <table className="w-full text-left text-sm">
//             <thead className="text-muted">
//               <tr>
//                 {[
//                   "Model",
//                   "Learning",
//                   "Accuracy",
//                   "Precision",
//                   "Recall",
//                   "F1",
//                   "ROC-AUC",
//                   "Fit time",
//                 ].map((h) => (
//                   <th key={h} className="py-2 pr-4 font-medium">
//                     {h}
//                   </th>
//                 ))}
//               </tr>
//             </thead>
//             <tbody>
//               {data.models.map((m) => (
//                 <tr
//                   key={m.name}
//                   className={`border-t border-line ${m.name === data.best_model ? "bg-brand-soft" : ""}`}
//                 >
//                   <td className="py-2 pr-4 font-medium">
//                     {m.name}
//                     {m.name === data.best_model && " ★"}
//                   </td>
//                   <td className="py-2 pr-4">
//                     <span
//                       className={`rounded px-2 py-0.5 text-xs ${m.mode === "online" ? "bg-brand text-white" : "bg-line text-ink"}`}
//                     >
//                       {m.mode === "online" ? "Online" : "Batch only"}
//                     </span>
//                   </td>
//                   <td className="py-2 pr-4">{m.final.accuracy.toFixed(3)}</td>
//                   <td className="py-2 pr-4">{m.final.precision.toFixed(3)}</td>
//                   <td className="py-2 pr-4">{m.final.recall.toFixed(3)}</td>
//                   <td className="py-2 pr-4">{m.final.f1.toFixed(3)}</td>
//                   <td className="py-2 pr-4">{m.final.roc_auc.toFixed(3)}</td>
//                   <td className="py-2 pr-4">{m.fit_seconds}s</td>
//                 </tr>
//               ))}
//             </tbody>
//           </table>
//         </div>
//         <p className="mt-3 text-xs text-muted">
//           Guessing &quot;no cancer&quot; every time would already score{" "}
//           {(data.baseline_accuracy * 100).toFixed(1)}% accuracy, so recall and
//           F1 matter as much as accuracy. ★ = best F1 among models that give
//           probabilities (used in Predict).
//         </p>
//       </Card>

//       <Card title="Comparison">
//         <div className="h-72">
//           <ResponsiveContainer width="100%" height="100%">
//             <BarChart data={chart}>
//               <CartesianGrid strokeDasharray="3 3" />
//               <XAxis dataKey="name" fontSize={11} />
//               <YAxis domain={[0, 1]} fontSize={11} />
//               <Tooltip />
//               <Legend />
//               <Bar dataKey="Accuracy" fill="#a1a1aa" />
//               <Bar dataKey="Recall" fill="#f87171" />
//               <Bar dataKey="F1" fill="#991b1b" />
//             </BarChart>
//           </ResponsiveContainer>
//         </div>
//       </Card>

//       <Card title={`Confusion matrix: ${best.name}`}>
//         <div className="grid max-w-sm grid-cols-2 gap-2 text-center text-sm">
//           <div className="rounded bg-line p-3">
//             True no cancer
//             <br />
//             <b>{best.final.tn}</b>
//           </div>
//           <div className="rounded bg-brand-soft p-3">
//             False alarm
//             <br />
//             <b>{best.final.fp}</b>
//           </div>
//           <div className="rounded bg-brand-soft p-3">
//             Missed cancer
//             <br />
//             <b>{best.final.fn}</b>
//           </div>
//           <div className="rounded bg-line p-3">
//             True cancer found
//             <br />
//             <b>{best.final.tp}</b>
//           </div>
//         </div>
//       </Card>
//     </div>
//   );
// }

"use client";

import { useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import Card from "./Card";
import ModelCard from "./ModelCard";
import { useApi } from "@/lib/useApi";
import type { Results } from "@/lib/types";
import { useAuth } from "@/lib/auth";

export default function ModelsTab({ dataset }: { dataset: string }) {
  const { data, error } = useApi<Results>(`/models/results?dataset=${dataset}`);
  const [updated, setUpdated] = useState<Results | null>(null);
  const results = updated ?? data;
  const { user } = useAuth();

  if (error) return <p className="text-sm text-brand">{error}</p>;
  if (!results) return <p className="text-sm text-muted">Loading…</p>;

  const chart = results.models.map((m) => ({
    name: m.name,
    Accuracy: m.final.accuracy,
    Recall: m.final.recall,
    F1: m.final.f1,
  }));

  return (
    <div className="space-y-6">
      <Card
        title={`All models at a glance (trained on ${(results.base_rows + results.stream_rows).toLocaleString()} rows, tested on ${results.test_rows.toLocaleString()})`}
      >
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chart}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" fontSize={11} />
              <YAxis domain={[0, 1]} fontSize={11} />
              <Tooltip />
              <Legend />
              <Bar dataKey="Accuracy" fill="#a1a1aa" />
              <Bar dataKey="Recall" fill="#f87171" />
              <Bar dataKey="F1" fill="#991b1b" />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <p className="mt-3 text-xs text-muted">
          Guessing &quot;no cancer&quot; every time would already score{" "}
          {(results.baseline_accuracy * 100).toFixed(1)}% accuracy, so recall
          and F1 matter as much as accuracy.
        </p>
      </Card>

      <div className="grid gap-4 xl:grid-cols-2">
        {results.models.map((m) => (
          <ModelCard
            key={m.name}
            model={m}
            isBest={m.name === results.best_model}
            dataset={dataset}
            onUpdated={setUpdated}
            canRetrain={user?.role === "admin"}
          />
        ))}
      </div>
    </div>
  );
}
