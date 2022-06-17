import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import TableCell from "@mui/material/TableCell";
import TableRow from "@mui/material/TableRow";
import { useCallback, useEffect, useState } from "react";
import { RunList } from "../components/RunList";
import Tags from "../components/Tags";
import { Run } from "../Models";
import Link from "@mui/material/Link";
import { RunListPayload } from "../Payloads";
import RunStateChip from "../components/RunStateChip";
import TimeAgo from "javascript-time-ago";

import ReactTimeAgo from "react-time-ago";
import en from "javascript-time-ago/locale/en.json";
import { Alert, AlertTitle, Container, useTheme } from "@mui/material";
import { InfoOutlined } from "@mui/icons-material";
import { RunTime } from "../components/RunTime";
import { pipelineSocket } from "../utils";

TimeAgo.addDefaultLocale(en);

function RecentStatuses(props: { runs: Array<Run> | undefined }) {
  let state: string | undefined = undefined;
  function statusChip(index: number) {
    if (props.runs && props.runs.length > index) {
      state = props.runs[index].future_state;
    } else {
      state = "undefined";
    }
    return <RunStateChip state={state} key={index} />;
  }
  return <>{[...Array(5)].map((e, i) => statusChip(i))}</>;
}

function PipelineRow(props: { run: Run }) {
  let run = props.run;

  const [runs, setRuns] = useState<Array<Run> | undefined>(undefined);

  useEffect(() => {
    let filters = JSON.stringify({
      calculator_path: { eq: run.calculator_path },
    });

    fetch("/api/v1/runs?limit=5&filters=" + filters)
      .then((res) => res.json())
      .then((result: RunListPayload) => {
        setRuns(result.content);
      });
  }, [run.calculator_path]);

  let endedAt = new Date();
  let endTimeString = run.failed_at || run.resolved_at;
  if (endTimeString) {
    endedAt = new Date(endTimeString);
  }

  return (
    <>
      <TableRow key={run.id}>
        <TableCell key="name">
          <Box sx={{ mb: 3 }}>
            <Link href={"/pipelines/" + run.calculator_path} underline="hover">
              <Typography variant="h6">{run.name}</Typography>
            </Link>
            <Typography fontSize="small" color="GrayText">
              <code>{run.calculator_path}</code>
            </Typography>
          </Box>
          <Tags tags={run.tags || []} />
        </TableCell>
        <TableCell key="last-run">
          {<ReactTimeAgo date={new Date(run.created_at)} locale="en-US" />}
          <RunTime run={run} />
        </TableCell>
        <TableCell key="status" width={120}>
          <RecentStatuses runs={runs} />
        </TableCell>
      </TableRow>
    </>
  );
}

function PipelineIndex() {
  const theme = useTheme();

  const triggerRefresh = useCallback((refreshCallback: () => void) => {
    pipelineSocket.removeAllListeners();
    pipelineSocket.on("update", (args) => {
      refreshCallback();
    });
  }, []);

  return (
    <Box sx={{ display: "grid", gridTemplateColumns: "1fr 300px" }}>
      <Box sx={{ gridColumn: 1 }}>
        <Container sx={{ pt: 15 }}>
          <Box sx={{ mx: 5 }}>
            <Box sx={{ mb: 10 }}>
              <Typography variant="h2" component="h2">
                Your pipelines
              </Typography>
            </Box>
            <RunList
              columns={["Name", "Last run", "Status"]}
              groupBy="calculator_path"
              filters={{ AND: [{ parent_id: { eq: null } }] }}
              emptyAlert="No pipelines."
              triggerRefresh={triggerRefresh}
            >
              {(run: Run) => <PipelineRow run={run} key={run.id} />}
            </RunList>
          </Box>
        </Container>
      </Box>
      <Box sx={{ gridColumn: 2, pr: 5, pt: 45 }}>
        <Alert severity="warning" icon={<InfoOutlined />}>
          <AlertTitle>Your latest pipelines are listed here</AlertTitle>
          <p>
            Pipelines are identified by the import path of their entry point,
            which is the function you called <code>.resolve()</code> on.
          </p>
        </Alert>
      </Box>
    </Box>
  );
}

export default PipelineIndex;
