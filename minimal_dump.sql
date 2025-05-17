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
-- Name: Course; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."Course" (
    id integer NOT NULL,
    name text NOT NULL,
    description text,
    date_start date,
    date_end date
);


--
-- Name: Course_activity; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."Course_activity" (
    id integer NOT NULL,
    user_id integer NOT NULL,
    course_id integer NOT NULL,
    role_id integer NOT NULL
);


--
-- Name: Course_activity_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."Course_activity_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: Course_activity_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."Course_activity_id_seq" OWNED BY public."Course_activity".id;


--
-- Name: Course_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."Course_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: Course_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."Course_id_seq" OWNED BY public."Course".id;


--
-- Name: Enrollment; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."Enrollment" (
    id integer NOT NULL,
    user_id integer NOT NULL,
    course_id integer NOT NULL
);


--
-- Name: Enrollment_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."Enrollment_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: Enrollment_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."Enrollment_id_seq" OWNED BY public."Enrollment".id;


--
-- Name: Roles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."Roles" (
    id integer NOT NULL,
    name text NOT NULL,
    description text
);


--
-- Name: Roles_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."Roles_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: Roles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."Roles_id_seq" OWNED BY public."Roles".id;


--
-- Name: Users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."Users" (
    id integer NOT NULL,
    tg_id integer NOT NULL,
    tg_hadle integer NOT NULL,
    name integer NOT NULL,
    last_name integer NOT NULL,
    chat_id integer NOT NULL
);


--
-- Name: Users_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."Users_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: Users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."Users_id_seq" OWNED BY public."Users".id;


--
-- Name: Course id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Course" ALTER COLUMN id SET DEFAULT nextval('public."Course_id_seq"'::regclass);


--
-- Name: Course_activity id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Course_activity" ALTER COLUMN id SET DEFAULT nextval('public."Course_activity_id_seq"'::regclass);


--
-- Name: Enrollment id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Enrollment" ALTER COLUMN id SET DEFAULT nextval('public."Enrollment_id_seq"'::regclass);


--
-- Name: Roles id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Roles" ALTER COLUMN id SET DEFAULT nextval('public."Roles_id_seq"'::regclass);


--
-- Name: Users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Users" ALTER COLUMN id SET DEFAULT nextval('public."Users_id_seq"'::regclass);


--
-- Data for Name: Course; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."Course" (id, name, description, date_start, date_end) FROM stdin;
\.


--
-- Data for Name: Course_activity; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."Course_activity" (id, user_id, course_id, role_id) FROM stdin;
\.


--
-- Data for Name: Enrollment; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."Enrollment" (id, user_id, course_id) FROM stdin;
\.


--
-- Data for Name: Roles; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."Roles" (id, name, description) FROM stdin;
\.


--
-- Data for Name: Users; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."Users" (id, tg_id, tg_hadle, name, last_name, chat_id) FROM stdin;
\.


--
-- Name: Course_activity_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."Course_activity_id_seq"', 1, false);


--
-- Name: Course_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."Course_id_seq"', 1, false);


--
-- Name: Enrollment_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."Enrollment_id_seq"', 1, false);


--
-- Name: Roles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."Roles_id_seq"', 1, false);


--
-- Name: Users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."Users_id_seq"', 1, false);


--
-- Name: Course_activity Course_activity_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Course_activity"
    ADD CONSTRAINT "Course_activity_pkey" PRIMARY KEY (id);


--
-- Name: Course Course_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Course"
    ADD CONSTRAINT "Course_pkey" PRIMARY KEY (id);


--
-- Name: Enrollment Enrollment_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Enrollment"
    ADD CONSTRAINT "Enrollment_pkey" PRIMARY KEY (id);


--
-- Name: Roles Roles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Roles"
    ADD CONSTRAINT "Roles_pkey" PRIMARY KEY (id);


--
-- Name: Users Users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Users"
    ADD CONSTRAINT "Users_pkey" PRIMARY KEY (id);


--
-- PostgreSQL database dump complete
--

