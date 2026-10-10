// // "use client";

// // import ComingSoon from "@/components/ComingSoon";
// // import ModelsTab from "@/components/ModelsTab";
// // import OnlineTab from "@/components/OnlineTab";
// // import OverviewTab from "@/components/OverviewTab";
// // import RequireAuth from "@/components/RequireAuth";
// // import UsersTab from "@/components/UsersTab";
// // import Workspace, { type WorkspaceTab } from "@/components/Workspace";
// // import AdminPredictionsTab from "@/components/AdminPredictionsTab";

// // const ReviewsSoon = () => (
// //   <ComingSoon title="Reviews and ratings" stage="Stage 4" />
// // );

// // const TABS: WorkspaceTab[] = [
// //   { id: "overview", label: "Overview", View: OverviewTab, needsDataset: false },
// //   { id: "users", label: "Users", View: UsersTab, needsDataset: false },
// //   {
// //     id: "predictions",
// //     label: "Predictions",
// //     View: AdminPredictionsTab,
// //     needsDataset: false,
// //   },
// //   {
// //     id: "models",
// //     label: "Models and retraining",
// //     View: ModelsTab,
// //     needsDataset: true,
// //   },
// //   {
// //     id: "online",
// //     label: "Online learning",
// //     View: OnlineTab,
// //     needsDataset: true,
// //   },
// //   { id: "reviews", label: "Reviews", View: ReviewsSoon, needsDataset: false },
// // ];

// // export default function AdminHome() {
// //   return (
// //     <RequireAuth role="admin">
// //       <Workspace title="Admin panel" tabs={TABS} />
// //     </RequireAuth>
// //   );
// // }

// "use client";

// import ActivityTab from "@/components/ActivityTab";
// import AdminPredictionsTab from "@/components/AdminPredictionsTab";
// import AdminReviewsTab from "@/components/AdminReviewsTab";
// import AnalyticsTab from "@/components/AnalyticsTab";
// import ModelsTab from "@/components/ModelsTab";
// import OnlineTab from "@/components/OnlineTab";
// import RequireAuth from "@/components/RequireAuth";
// import UsersTab from "@/components/UsersTab";
// import Workspace, { type WorkspaceTab } from "@/components/Workspace";

// const TABS: WorkspaceTab[] = [
//   {
//     id: "analytics",
//     label: "Analytics",
//     View: AnalyticsTab,
//     needsDataset: false,
//   },
//   { id: "users", label: "Users", View: UsersTab, needsDataset: false },
//   {
//     id: "predictions",
//     label: "Predictions",
//     View: AdminPredictionsTab,
//     needsDataset: false,
//   },
//   {
//     id: "activity",
//     label: "Activity log",
//     View: ActivityTab,
//     needsDataset: false,
//   },
//   {
//     id: "reviews",
//     label: "Reviews",
//     View: AdminReviewsTab,
//     needsDataset: false,
//   },
//   {
//     id: "models",
//     label: "Models and retraining",
//     View: ModelsTab,
//     needsDataset: true,
//   },
//   {
//     id: "online",
//     label: "Online learning",
//     View: OnlineTab,
//     needsDataset: true,
//   },
// ];

// export default function AdminHome() {
//   return (
//     <RequireAuth role="admin">
//       <Workspace title="Admin panel" tabs={TABS} />
//     </RequireAuth>
//   );
// }

"use client";

import ActivityTab from "@/components/ActivityTab";
import AdminPredictionsTab from "@/components/AdminPredictionsTab";
import AdminReviewsTab from "@/components/AdminReviewsTab";
import AnalyticsTab from "@/components/AnalyticsTab";
import LiveLearningTab from "@/components/LiveLearningTab";
import ModelsTab from "@/components/ModelsTab";
import OnlineTab from "@/components/OnlineTab";
import OutcomesTab from "@/components/OutcomesTab";
import RequireAuth from "@/components/RequireAuth";
import UsersTab from "@/components/UsersTab";
import Workspace, { type WorkspaceTab } from "@/components/Workspace";

const TABS: WorkspaceTab[] = [
  {
    id: "analytics",
    label: "Analytics",
    View: AnalyticsTab,
    needsDataset: false,
  },
  { id: "users", label: "Users", View: UsersTab, needsDataset: false },
  {
    id: "predictions",
    label: "Predictions",
    View: AdminPredictionsTab,
    needsDataset: false,
  },
  { id: "outcomes", label: "Outcomes", View: OutcomesTab, needsDataset: false },
  {
    id: "live",
    label: "Live learning",
    View: LiveLearningTab,
    needsDataset: true,
  },
  {
    id: "activity",
    label: "Activity log",
    View: ActivityTab,
    needsDataset: false,
  },
  {
    id: "reviews",
    label: "Reviews",
    View: AdminReviewsTab,
    needsDataset: false,
  },
  {
    id: "models",
    label: "Models and retraining",
    View: ModelsTab,
    needsDataset: true,
  },
  {
    id: "online",
    label: "Learning replay",
    View: OnlineTab,
    needsDataset: true,
  },
];

export default function AdminHome() {
  return (
    <RequireAuth role="admin">
      <Workspace title="Admin panel" tabs={TABS} />
    </RequireAuth>
  );
}
