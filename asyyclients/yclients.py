# coding=utf-8
import datetime
import time
import httpx
import pandas as pd
import ujson


class AsyncYClientsAPI:

    def __init__(self, token: str, company_id: int, form_id: int, language: str = 'ru-RU'):
        self.company_id = company_id
        self.form_id = form_id
        self.headers = {
            "Accept": "application/vnd.yclients.v2+json",
            'Accept-Language': language,
            'Authorization': "Bearer {}".format(token),
            'Cache-Control': "no-cache"
        }
        # if __show_debugging==True code will show debugging process
        self.__show_debugging = False

    @staticmethod
    def datetime_parser(date_time: str) -> datetime.datetime:
        """ datetime in iso8601 format parser """
        a, b = date_time.split('+')
        dt = datetime.datetime.strptime(a, "%Y-%m-%dT%H:%M:%S")
        return dt

    async def book(self, booking_id: int, fullname: str, phone: str, email: str, staff_id: int,
                   date_time: str | datetime.datetime,
                   service_id: int = None, comment: str = None) -> (True, None) or (False, Exception):
        """ Make booking """
        url = "https://n{}.yclients.com/api/v1/book_record/{}/".format(self.form_id, self.company_id)
        payload = {
            "phone": phone,
            "fullname": fullname,
            "email": email,
            "comment": comment,
            "notify_by_email": 0,
            "appointments": [{
                "id": booking_id,
                "services": [int(service_id)],
                "staff_id": int(staff_id or 0),
                "datetime": date_time
            }]
        }
        async with httpx.AsyncClient() as c:
            response = await c.post(url, json=payload, headers=self.headers)
        res = ujson.loads(response.text)
        if isinstance(res, dict) and res.get('errors'):
            return False, res.get('errors', {}).get('message', '')
        return True, ''

    async def get_staff_info(self, staff_id: int) -> dict:
        """ Return dict with info about specific staff"""
        url = "https://n{}.yclients.com/api/v1/staff/{}/{}".format(self.form_id, self.company_id, staff_id)
        async with httpx.AsyncClient() as c:
            response = await c.get(url, headers=self.headers)
        return ujson.loads(response.text)

    async def get_service_info(self, service_id: int) -> dict:
        """ Return dict with info about specific service"""
        url = "https://n{}.yclients.com/api/v1/services/{}/{}".format(self.form_id, self.company_id, service_id)
        async with httpx.AsyncClient() as c:
            response = await c.get(url, headers=self.headers)
        return ujson.loads(response.text)

    async def get_staff(self, service_id: int = None, date_time=None) -> dict:
        """ Return dict of staff for specific service and date"""
        url = "https://n{}.yclients.com/api/v1/book_staff/{}".format(self.form_id, self.company_id)
        querystring = {"service_ids[]": int(service_id)} if service_id else {}
        querystring.update({"datetime": date_time} if date_time else {})
        async with httpx.AsyncClient() as c:
            response = await c.get(url, headers=self.headers, params=querystring)
        return ujson.loads(response.text)

    async def get_services(self, staff_id: int = None, date_time: int = None) -> dict:
        """ Return list of services for specific staff and date"""
        url = "https://n{}.yclients.com/api/v1/book_services/{}".format(self.form_id, self.company_id)
        querystring = {"staff_id": int(staff_id)} if staff_id else {}
        querystring.update({"datetime": date_time} if date_time else {})
        async with httpx.AsyncClient() as c:
            response = await c.get(url, headers=self.headers, params=querystring)
        return ujson.loads(response.text)

    async def get_available_days(self, staff_id: int = None, service_id: int = None) -> dict:
        """ Return all available days for specific staff and service"""
        url = "https://n{}.yclients.com/api/v1/book_dates/{}".format(self.form_id, self.company_id)
        querystring = {"staff_id": int(staff_id)} if staff_id else {}
        querystring.update({"service_ids[]": service_id} if service_id else {})
        async with httpx.AsyncClient() as c:
            response = await c.get(url, headers=self.headers, params=querystring)
        return ujson.loads(response.text)

    async def get_available_times(self, staff_id: int, service_id: int = None, day=None) -> dict:
        """ Return all available time slots on specific day staff and service"""
        url = "https://n{}.yclients.com/api/v1/book_times/{}/{}/{}".format(self.form_id, self.company_id, staff_id, day)
        querystring = {}
        if service_id:
            querystring.update({"service_ids[]": service_id})
        async with httpx.AsyncClient() as c:
            response = await c.request("GET", url, headers=self.headers, params=querystring)
        return ujson.loads(response.text)

    """DEBUGGING"""

    def show_debugging(self):
        print("Debugging prints turned on")
        self.__show_debugging = True

    def hide_debugging(self):
        print("Debugging prints turned off")
        self.__show_debugging = False

    """USER AUTHORIZATION"""

    async def get_user_token(self, login: str, password: str) -> str:
        """
        To read clients data you need to obtain user token
        :param login: yclients user login
        :param password: yclients user login
        :return: user token
        """
        url = "https://api.yclients.com/api/v1/auth"
        querystring = {
            "login": login,
            "password": password
        }
        async with httpx.AsyncClient() as c:
            response = await c.post(url, headers=self.headers, params=querystring)
        user_token = ujson.loads(response.text)['data']['user_token']
        if self.__show_debugging:
            print(f"Obtained user token {user_token}")
        return user_token

    def update_user_token(self, user_token: str):
        """
        After user token was obtained you need to include it in
        header of requests that you are sending
        :param user_token: user token
        :return:
        """
        self.headers['Authorization'] = \
            self.headers['Authorization'] + f", User {user_token}"
        if self.__show_debugging:
            print(f"Updated autorisation parameters:"
                  f" {self.headers['Authorization']}")

    async def show_user_permissions(self):
        """
        :return: json-type data with user permissions
        """
        url = f"https://api.yclients.com/api/v1/user/permissions/{self.company_id}"
        querystring = {}
        async with httpx.AsyncClient() as c:
            response = await c.request("GET", url, headers=self.headers, params=querystring)
        data = ujson.loads(response.text)['data']
        print("User permissions:")
        print(ujson.dumps(data, indent=4, sort_keys=True))
        return data

    """CLIENTS DATA"""

    async def __get_clients_page(self, page_number: int, session: httpx.AsyncClient, clients_per_page: int) -> dict:
        """
        Yclients api can't return all clients at once and returns in groups
         of maximum size of 200. Those groups are called pages and you can
         choose how many clients it will return
        :param page_number: number of page
        :param session: httpx.Client() object
        :param clients_per_page: size of the page
        :return: data of clients on the page page_number
        """
        st = time.time()
        url = "https://api.yclients.com/api/v1/clients/{}".format(self.company_id)
        querystring = {}
        querystring.update({"count": clients_per_page})
        querystring.update({"page": page_number})
        response = await session.get(url, headers=self.headers, params=querystring)
        if self.__show_debugging:
            print(f'Clients page {page_number} obtained in {time.time() - st} sec')
        return ujson.loads(response.text)

    async def get_clients_data(self, clients_per_page: int = 200) -> dict:
        """
        :param clients_per_page: size of the page
        :return: data of all the clients in the system
            client's parameters:
            'id', 'name', 'phone', 'email', 'card',
             'birth_date', 'comment', 'discount', 'visits',
              'sex_id', 'sex', 'sms_check', 'sms_bot', 'spent',
               'paid', 'balance', 'importance_id', 'importance',
                'categories', 'last_change_date', 'custom_fields'
        """
        async with httpx.AsyncClient(trust_env=False) as session:
            # In the first request we obtain total number of clients in system
            first_request = await self.__get_clients_page(1, session, clients_per_page)
            clients_data_list = first_request['data']

            # total number of clients
            clients_number = first_request['meta']['total_count']

            # number of pages that we need to request
            pages_number = int(clients_number / clients_per_page) + 1
            if self.__show_debugging:
                print(f"There are {clients_number} clients in the system")
                if pages_number > 1:
                    print(f"{pages_number} pages will be loaded")

            if pages_number == 1:
                return clients_data_list

            for page in range(2, pages_number + 1):
                new_page_request = await self.__get_clients_page(page, session, clients_per_page)
                clients_data_list.extend(new_page_request['data'])
            return clients_data_list

    def parse_clients_data(self, clients_data_list: list) -> pd.DataFrame:
        """
        :param clients_data_list: list of dictionaries with client data
        :return: pd.Dataframe with clients data
        """
        columns = clients_data_list[0].keys()
        df = pd.DataFrame(columns=columns)
        for client_data in clients_data_list:
            df = df.append(client_data, ignore_index=True)
        if self.__show_debugging:
            print("Parsed clients data:")
            print(df)
        return df

    """VISITS DATA"""

    async def __get_visits_page(self, cid: int, page_number: int, session: httpx.AsyncClient, visits_per_page: int) -> dict:
        """
        Yclients api can't return all visits at once and returns in groups
         of maximum size of 200. Those groups are called pages and you can
         choose how many visits it will return
        :param page_number: number of page
        :param session: requests.Session() object
        :param visits_per_page: size of the page
        :return: data of visits on the page page_number
        """
        st = time.time()
        url = f"https://api.yclients.com/api/v1/records/{self.company_id}"
        querystring = {
            "client_id": cid,
            "count": visits_per_page,
            "page": page_number
        }
        response = await session.get(url, headers=self.headers, params=querystring)
        if self.__show_debugging:
            print(f'Visits page {page_number} obtained in {time.time() - st} sec')

        return ujson.loads(response.text)

    async def get_visits_for_client(self, cid: int, visits_per_page: int = 200, session: httpx.AsyncClient = None) -> list:
        """
        :param cid: client id
        :param visits_per_page: size of the page
        :param session: None by default, but if we get visits for multiple clients,
            we want to use the same session for all of them
        :return: data of all the visits of client cid
            visit parameters:
                 id, company_id, staff_id, services, goods_transactions,
                 staff, client, comer, clients_count, date, datetime,
                 create_date, comment, online, visit_attendance, attendance,
                 confirmed, seance_length, length, sms_before, sms_now,
                 sms_now_text, email_now, notified, master_request, api_id,
                 from_url, review_requested, visit_id, created_user_id,
                 deleted, paid_full, prepaid, prepaid_confirmed,
                 last_change_date, custom_color, custom_font_color, record_labels,
                 activity_id, custom_fields, documents, is_sale_bill_printed,
            Also some fields include additional information:
            - client is a dictionary with parameters:
                'id', 'name', 'phone', 'card', 'email',
                'success_visits_count', 'fail_visits_count', 'discount'
            - documents include list of dictionaries with parameters:
                'id', 'type_id', 'storage_id', 'user_id', 'company_id',
                'number', 'comment', 'date_created', 'category_id',
                'visit_id', 'record_id', 'type_title'
            - services include list of dictionaries with parameters:
                'id', 'title', 'cost', 'manual_cost', 'cost_per_unit',
                'discount', 'first_cost', 'amount'
            - staff is a dictionary with parameters:
                'id', 'api_id', 'name', 'specialization', 'position',
                'avatar', 'avatar_big', 'rating', 'votes_count'
                - position is a dictionary with parameters:
                    'id', 'title'
            Parameters description is  accesible via:
            https://github.com/petroff/api-blueprint/blob/master/apiary.apib
        """
        if not session:
            session = httpx.AsyncClient(trust_env=False)

        with session:

            # In the first request we obtain total number of client visits in system
            first_request = await self.__get_visits_page(cid=cid,
                                                   page_number=1,
                                                   session=session,
                                                   visits_per_page=visits_per_page)
            visits_data_list = first_request['data']
            # total number of visits
            visits_number = first_request['meta']['total_count']
            # number of pages that we need to request
            pages_number = int(visits_number / visits_per_page) + 1
            if self.__show_debugging:
                print(f"There are {visits_number} visits for clients {cid} in the system")
                if pages_number > 1:
                    print(f"{pages_number} pages will be loaded")

            if pages_number == 1:
                return visits_data_list

            for page in range(2, pages_number + 1):
                new_page_request = await self.__get_visits_page(cid=cid,
                                                          page_number=page,
                                                          session=session,
                                                          visits_per_page=visits_per_page)
                visits_data_list.extend(new_page_request['data'])
            return visits_data_list

    async def get_visits_data_for_clients_list(self, cids_list: list, visits_per_page=200) -> dict:
        """
        get_visits_for_client funtion wrapper for multiple clients
        :param cids_list: list of clients ids
        :param visits_per_page: size of the page
        :return: dictionary with client id as key and list of visits as value
        """
        session = httpx.AsyncClient(trust_env=False)

        clients_visits_dictionary = {cid: await self.get_visits_for_client(cid, visits_per_page, session)
                                     for cid in cids_list}
        return clients_visits_dictionary

    async def get_attended_visits_for_client(self, cid: int, visits_per_page: int = 200,
                                       session: httpx.AsyncClient = None) -> list:
        """
        Attendance explanation from Yclient API:
            2 - The user has confirmed the entry,
            1 - The user has arrived, the services are provided,
            0 - the user is waiting,
            -1 - the user did not come for a visit
        :param cid: client id
        :param visits_per_page: size of the page
        :param session: None by default, but if we get visits for multiple clients,
            we want to use the same session for all of them
        :return: data of all the visits of client cid where attendance field is equal to 1
        """
        all_visits = await self.get_visits_for_client(cid=cid,
                                                visits_per_page=visits_per_page,
                                                session=session)
        attended_visits = [visit for visit in all_visits if visit['attendance'] == 1]

        return attended_visits

    async def get_attended_visits_dates_information(self, cids_lists: list, visits_per_page: int = 200,
                                              session: httpx.AsyncClient = None) -> pd.DataFrame:
        """
        :param cids_lists: clients ids list
        :param visits_per_page: size of the page
        :param session: None by default, but if we get visits for multiple clients,
            we want to use the same session for all of them
        :return: Dataframe with columns:
            - id: client id
            - visits_number: number of attended visits
            - first_visit: date of client first attended visit
            - last_visit: date of client last attended visit
        """
        columns = ['id', 'visits_number', 'first_visit', 'last_visit']
        df = pd.DataFrame(columns=columns)
        for cid in cids_lists:
            c_dict = {'id': cid}
            attended_visits = await self.get_attended_visits_for_client(cid=cid,
                                                                        visits_per_page=visits_per_page,
                                                                        session=session
                                                                        )
            visit_dates = [visit['datetime'] for visit in attended_visits]

            if not visit_dates:
                c_dict['visits_number'] = 0
                c_dict['first_visit'] = None
                c_dict['last_visit'] = None
            else:
                visit_dates = list(map(self.datetime_parser, visit_dates))
                c_dict['visits_number'] = len(visit_dates)
                c_dict['first_visit'] = min(visit_dates).date()
                c_dict['last_visit'] = max(visit_dates).date()

            df = df.append(c_dict, ignore_index=True)
        return df
