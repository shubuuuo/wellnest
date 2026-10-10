// "use client";

// import ChatTab from "@/components/ChatTab";
// import DatasetTab from "@/components/DatasetTab";
// import ModelsTab from "@/components/ModelsTab";
// import PredictTab from "@/components/PredictTab";
// import RequireAuth from "@/components/RequireAuth";
// import Workspace, { type WorkspaceTab } from "@/components/Workspace";

// import HistoryTab from "@/components/HistoryTab";
// import ProfileTab from "@/components/ProfileTab";

// const TABS: WorkspaceTab[] = [
//   {
//     id: "predict",
//     label: "Check my risk",
//     View: PredictTab,
//     needsDataset: true,
//   },
//   { id: "history", label: "My history", View: HistoryTab, needsDataset: false },
//   {
//     id: "profile",
//     label: "Health profile",
//     View: ProfileTab,
//     needsDataset: false,
//   },
//   { id: "dataset", label: "Dataset", View: DatasetTab, needsDataset: true },
//   { id: "models", label: "Models", View: ModelsTab, needsDataset: true },
//   { id: "chat", label: "Assistant", View: ChatTab, needsDataset: true },
//   {
//     id: "predict",
//     label: "Check my risk",
//     View: PredictTab,
//     needsDataset: true,
//   },
//   { id: "dataset", label: "Dataset", View: DatasetTab, needsDataset: true },
//   { id: "models", label: "Models", View: ModelsTab, needsDataset: true },
//   { id: "chat", label: "Assistant", View: ChatTab, needsDataset: true },
// ];

// export default function UserHome() {
//   return (
//     <RequireAuth>
//       <Workspace title="Health checks" tabs={TABS} />
//     </RequireAuth>
//   );
// }

"use client";

import ChatTab from "@/components/ChatTab";
import DatasetTab from "@/components/DatasetTab";
import HistoryTab from "@/components/HistoryTab";
import ModelsTab from "@/components/ModelsTab";
import PredictTab from "@/components/PredictTab";
import ProfileTab from "@/components/ProfileTab";
import RequireAuth from "@/components/RequireAuth";
import Workspace, { type WorkspaceTab } from "@/components/Workspace";
import ReviewTab from "@/components/ReviewTab";

const TABS: WorkspaceTab[] = [
  {
    id: "predict",
    label: "Check my risk",
    View: PredictTab,
    needsDataset: true,
  },
  { id: "history", label: "My history", View: HistoryTab, needsDataset: false },
  {
    id: "profile",
    label: "Health profile",
    View: ProfileTab,
    needsDataset: false,
  },
  { id: "dataset", label: "Dataset", View: DatasetTab, needsDataset: true },
  { id: "models", label: "Models", View: ModelsTab, needsDataset: true },
  { id: "chat", label: "Assistant", View: ChatTab, needsDataset: true },
  { id: "feedback", label: "Feedback", View: ReviewTab, needsDataset: false },
];

export default function UserHome() {
  return (
    <RequireAuth>
      <Workspace title="Health checks" tabs={TABS} />
    </RequireAuth>
  );
}
