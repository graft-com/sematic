import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import useAsyncFn from "react-use/lib/useAsyncFn";
import useList from "react-use/lib/useList";
import useLatest from "react-use/lib/useLatest";
import { LogLineRequestResponse } from "../Payloads";
import { AsyncInvocationQueue, useLogger } from "src/utils";
import { useHttpClient } from "./httpHooks";

const MAX_LINES = 2000;
const POLLING_INTERVAL = 5000;
export interface GetNextResult {
    pulledLines: number
}

export enum DiagnosticReasons {
    BOOTSTRAP = "BOOTSTRAP",
    SCROLL = "SCROLL",
    PULLDOWN = "PULLDOWN",
    ACCUMULATE = "ACCUMULATE"
} 

export function useLogStream(source: string, filterString: string) {
    const [lines, {push: pushLines}] = useList<string>([]);
    const [cursor, setCursor] = useState<string | null>(null);
    const [logInfoMessage, setlogInfoMessage] = useState<string | null>(null);
    const [hasPulledData, setHasPulledData] = useState(false);

    const hasMore = useMemo(() => {
        return !hasPulledData || cursor != null;
    }, [cursor, hasPulledData]);

    const { fetch } = useHttpClient();
    const { devLogger } = useLogger();

    const FetchOccurenceCounters = useRef({
        [DiagnosticReasons.BOOTSTRAP]: 0,
        [DiagnosticReasons.SCROLL]: 0,
        [DiagnosticReasons.PULLDOWN]: 0,
        [DiagnosticReasons.ACCUMULATE]: 0    
    });

    const [{ loading: isLoading, error }, getNext] = useAsyncFn(
        async (reason: DiagnosticReasons): Promise<GetNextResult> => {
            FetchOccurenceCounters.current[reason] += 1;
            const occurenceID = FetchOccurenceCounters.current[reason];
            const DEBUG_TAG = `${reason}_${occurenceID}`;
            devLogger(`logHooks.ts [${DEBUG_TAG}] getNext() started. hasMore ${hasMore} `
                + `cursor: ${cursor && atob(cursor)} filter_string: ${filterString}`);
            let queryParams: any = {
                'DEBUG': DEBUG_TAG,
                max_lines: '' + MAX_LINES
            };

            if (!!cursor) {
                queryParams['continuation_cursor'] = cursor;
            }
            if (!!filterString) {
                queryParams['filter_string'] = filterString;
            }

            const qString = (new URLSearchParams(queryParams)).toString();
            const url = `/api/v1/runs/${source}/logs?${qString}`;

            const payload: LogLineRequestResponse = await (await fetch({ url })).json();

            const { content: { lines, continuation_cursor, log_info_message } } = payload;

            devLogger(`logHooks.ts [${DEBUG_TAG}] getNext() ${url} completed. `
                + `# of lines: ${(!!lines ? lines.length : NaN)} `
                + `continuation_cursor: ${continuation_cursor && atob(continuation_cursor)} `
                + `log_info_message: ${log_info_message || 'N/A'} `);

            pushLines(...lines);
            setCursor(continuation_cursor);
            setlogInfoMessage(log_info_message);
            setHasPulledData(true);
            return {
                pulledLines: lines.length
            }
        }, [source, setHasPulledData, hasMore, filterString, cursor, MAX_LINES, devLogger]);

    const acquire = useRef(AsyncInvocationQueue());

    const getNextLatest = useLatest(getNext);

    // This is a function to call getNext by queuing the request.
    // This is to avoid multiple getNext() calls being made at the same time.
    const getNextWithQueue = useCallback(async (reason: DiagnosticReasons) => {
        const release = await acquire.current();
        const result = await getNextLatest.current(reason);
        release();
        return result;
    },[acquire, getNextLatest]);

    return { lines, isLoading, error, hasMore, logInfoMessage, getNext: getNextWithQueue, hasPulledData };
}

export function useAccumulateLogsUntilEnd(hasMore: boolean, 
    getNext: (reason: DiagnosticReasons) => Promise<GetNextResult>) {
    // useLatest() ensures that the multi-stage async function always see the 
    // latest state of those variables, instead of the state attached to the 
    // function closure at the beginning.
    const latestHasMore = useLatest(hasMore);
    const latestGetNext = useLatest(getNext);
    const [isAccumulating, setIsAccumulating] = useState(false);
    const [accumulatedLines, setAccumulatedLines] = useState<number>(0);
    const [isLoading, setIsLoading] = useState(false);

    const abortControllerRef = useRef<AbortController | null>(null);
    const { devLogger } = useLogger();

    const cancelAccumulation = useCallback(() => {
        if (!!abortControllerRef.current) {
            abortControllerRef.current.abort();
            devLogger('Logs accumulation aborted.')
        }
    }, [abortControllerRef, devLogger]);

    const accumulateLogsUntilEnd = useCallback(async () => {
        setIsAccumulating(true);
        let accumulatedLines = 0;
        setAccumulatedLines(accumulatedLines);

        const abortController = new AbortController();
        abortControllerRef.current = abortController;
        while(latestHasMore.current === true) {
            if (abortController.signal.aborted) {
                break;
            }

            setIsLoading(true);
            const {pulledLines} = await latestGetNext.current(DiagnosticReasons.ACCUMULATE);

            if (abortController.signal.aborted) {
                break;
            }
            setIsLoading(false);
            
            // The server shouldn't return NaN, but just in case and be defensive,
            // we don't want to add NaN to the accumulatedLines.
            if (!isNaN(pulledLines)) {
                accumulatedLines += pulledLines;
                setAccumulatedLines(accumulatedLines);
            }

            // Yield to rendering cycles
            await new Promise(
                resolve => setTimeout(resolve, POLLING_INTERVAL)
            );
        }
        setIsAccumulating(false);
    }, [latestHasMore, latestGetNext]);

    useEffect(() => {
        // always cancel ongoing accumulation if the component will unmount
        return () => {
            cancelAccumulation();
        }
    }, [cancelAccumulation])

    return {
        accumulateLogsUntilEnd,
        isAccumulating,
        isLoading,
        accumulatedLines
    };
}