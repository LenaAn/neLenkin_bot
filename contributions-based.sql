--
-- PostgreSQL database dump
--

-- Dumped from database version 17.4 (Debian 17.4-1.pgdg120+2)
-- Dumped by pg_dump version 17.4 (Debian 17.4-1.pgdg120+2)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: Contribution_type; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."Contribution_type" (
    id integer NOT NULL,
    contribution_type_name text NOT NULL,
    contribution_type_description text
);


ALTER TABLE public."Contribution_type" OWNER TO postgres;

--
-- Name: Contribution_type_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public."Contribution_type_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public."Contribution_type_id_seq" OWNER TO postgres;

--
-- Name: Contribution_type_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public."Contribution_type_id_seq" OWNED BY public."Contribution_type".id;


--
-- Name: Contributions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."Contributions" (
    id integer NOT NULL,
    user_id integer NOT NULL,
    course_id integer NOT NULL,
    contribution_type_id integer NOT NULL,
    date date NOT NULL
);


ALTER TABLE public."Contributions" OWNER TO postgres;

--
-- Name: Contributions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public."Contributions_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public."Contributions_id_seq" OWNER TO postgres;

--
-- Name: Contributions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public."Contributions_id_seq" OWNED BY public."Contributions".id;


--
-- Name: Course; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."Course" (
    id integer NOT NULL,
    name text NOT NULL,
    description text,
    date_start date,
    date_end date
);


ALTER TABLE public."Course" OWNER TO postgres;

--
-- Name: Course_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public."Course_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public."Course_id_seq" OWNER TO postgres;

--
-- Name: Course_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public."Course_id_seq" OWNED BY public."Course".id;


--
-- Name: Enrollment; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."Enrollment" (
    id integer NOT NULL,
    user_id integer NOT NULL,
    course_id integer NOT NULL
);


ALTER TABLE public."Enrollment" OWNER TO postgres;

--
-- Name: Enrollment_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public."Enrollment_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public."Enrollment_id_seq" OWNER TO postgres;

--
-- Name: Enrollment_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public."Enrollment_id_seq" OWNED BY public."Enrollment".id;


--
-- Name: Users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."Users" (
    id integer NOT NULL,
    tg_id integer NOT NULL,
    tg_hadle integer NOT NULL,
    name integer NOT NULL,
    last_name integer NOT NULL,
    chat_id integer NOT NULL
);


ALTER TABLE public."Users" OWNER TO postgres;

--
-- Name: Users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public."Users_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public."Users_id_seq" OWNER TO postgres;

--
-- Name: Users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public."Users_id_seq" OWNED BY public."Users".id;


--
-- Name: Contribution_type id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Contribution_type" ALTER COLUMN id SET DEFAULT nextval('public."Contribution_type_id_seq"'::regclass);


--
-- Name: Contributions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Contributions" ALTER COLUMN id SET DEFAULT nextval('public."Contributions_id_seq"'::regclass);


--
-- Name: Course id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Course" ALTER COLUMN id SET DEFAULT nextval('public."Course_id_seq"'::regclass);


--
-- Name: Enrollment id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Enrollment" ALTER COLUMN id SET DEFAULT nextval('public."Enrollment_id_seq"'::regclass);


--
-- Name: Users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Users" ALTER COLUMN id SET DEFAULT nextval('public."Users_id_seq"'::regclass);


--
-- Data for Name: Contribution_type; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public."Contribution_type" (id, contribution_type_name, contribution_type_description) FROM stdin;
1	Present_topic	Present a chapter of a book or algo topic or smth
3	Graduate	Usually granted when someone attended > 70% of a course
2	Coordinate course	Coordinate a while course. The date of this type is the start of the course
\.


--
-- Data for Name: Contributions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public."Contributions" (id, user_id, course_id, contribution_type_id, date) FROM stdin;
\.


--
-- Data for Name: Course; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public."Course" (id, name, description, date_start, date_end) FROM stdin;
1	DDIA-1	First course for reading DDIA	2024-06-06	2024-10-03
2	DDIA-2	Second stream of reading DDIA	2024-10-12	2025-03-01
3	DDIA-3	Third stream of reading DDIA	2025-03-13	\N
4	DDIA-combined	Some people didn't graduate from a single stream, but attended enough calls in several streams combined	\N	\N
5	Advent-Of-Code-2024	December 2024 advent of Code. Doesn't have 	2024-12-01	2024-12-25
6	LeetCode-Grind	Solving Leetcode 75	2024-10-17	2025-02-13
7	LeetCode-Mock-Club	Leetcode mocks, every week new topic	2025-02-24	\N
8	SRE-book	Reading SRE book	2025-03-11	\N
\.


--
-- Data for Name: Enrollment; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public."Enrollment" (id, user_id, course_id) FROM stdin;
\.


--
-- Data for Name: Users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public."Users" (id, tg_id, tg_hadle, name, last_name, chat_id) FROM stdin;
\.


--
-- Name: Contribution_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public."Contribution_type_id_seq"', 3, true);


--
-- Name: Contributions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public."Contributions_id_seq"', 1, false);


--
-- Name: Course_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public."Course_id_seq"', 8, true);


--
-- Name: Enrollment_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public."Enrollment_id_seq"', 1, false);


--
-- Name: Users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public."Users_id_seq"', 1, false);


--
-- Name: Contribution_type Contribution_type_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Contribution_type"
    ADD CONSTRAINT "Contribution_type_pkey" PRIMARY KEY (id);


--
-- Name: Contributions Contributions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Contributions"
    ADD CONSTRAINT "Contributions_pkey" PRIMARY KEY (id);


--
-- Name: Course Course_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Course"
    ADD CONSTRAINT "Course_pkey" PRIMARY KEY (id);


--
-- Name: Enrollment Enrollment_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Enrollment"
    ADD CONSTRAINT "Enrollment_pkey" PRIMARY KEY (id);


--
-- Name: Users Users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Users"
    ADD CONSTRAINT "Users_pkey" PRIMARY KEY (id);


--
-- PostgreSQL database dump complete
--

