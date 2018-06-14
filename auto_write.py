import os


class AutoWrite:

    def __init__(self, debug=True):

        self.BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.CUR_DIR = os.path.split(__file__)[0]
        self.dir_list = [self.BASE_DIR]
        self.views_list = []
        self.main(debug)

    def __search_all_views(self):

        while len(self.dir_list) != 0:

            dir_path = self.dir_list.pop()
            file_list = os.listdir(dir_path)
            cur_path = dir_path

            for file in file_list:

                if file[0] == '.':
                    continue

                file_path = os.path.join(cur_path, file)

                if os.path.isdir(file_path):
                    if file not in ['templates', 'static']:
                        self.dir_list.append(file_path)

                elif file == 'views.py':
                    self.views_list.append(file_path)

    def __parser_views(self):
        views = []
        for view in self.views_list:
            ret = self.__parser_view(view)
            if ret is not None:
                views.append(ret)
        return views

    def __parser_view(self, view_path):

        view_list = []
        with open(view_path, 'r', encoding='UTF-8') as view:
            lines = view.readlines()
            if len(lines) == 0:
                return None
            for line in lines:
                ret = self.__parser_lines(line)
                if ret is not None:
                    view_list.append(ret)
        return {'view_file': view_path, 'view_list': view_list}

    @staticmethod
    def __parser_lines(line):

        ret = None
        if 'def' in line and '(request' in line and '):' in line:
            line = line.replace('def', '').replace('(request', '').replace('):', '').replace(' ', '').replace('\n', '')
            params = line.split(',')
            view_name = params[0]
            args = []
            if len(params) > 1:
                _args = params[1:]
                for arg in _args:
                    if '=' in arg:
                        k, v = arg.split('=')
                    else:
                        k = arg
                    args.append(k)
            ret = {'view_name': view_name, 'args': args}

        return ret

    def main(self, debug):

        if not debug:
            return

        self.__search_all_views()
        if len(self.views_list) == 0:
            assert 'not find views.py or views.py is empty'
        print("view_list", end='')
        print(self.views_list)
        views = self.__parser_views()
        for view in views:
            for k, v in view.items():
                print(k + ":")
                print(v)
            print('---------------------------------------')

        self.__add_path(views)
        self.__add_templates(views)
        print('write finish!')

    def __add_path(self, views):

        for view in views:
            view_file = view['view_file']
            view_list = view['view_list']
            dir_path = os.path.split(view_file)[0]
            app_name = os.path.split(dir_path)[1]

            if os.path.exists(os.path.join(dir_path, 'urls.py')):
                print('app下存在urls.py')
                print(dir_path)
                self.parse_urls(app_name, dir_path, view_list)
                # self.__add_urls_path(app_name, dir_path, view_list)
            else:
                self.parse_urls(app_name, self.CUR_DIR, view_list)
                # self.__add_urls_path(app_name, self.CUR_DIR, view_list)

    def __add_templates(self, views):

        for _view in views:

            view_file = _view['view_file']
            view_list = _view['view_list']
            dir_path = os.path.split(view_file)[0]
            app_name = os.path.split(dir_path)[1]
            template_path = os.path.join(self.BASE_DIR, 'templates')
            # app_template_path = os.path.join(template_path, app_name)
            if not os.path.exists(template_path):
                assert 'templates not found'

            # if not os.path.exists(app_template_path):
            #     os.mkdir(app_template_path)

            for view in view_list:

                view_name = view['view_name']
                view_path = os.path.join(template_path, view_name + '.html')

                if not os.path.exists(view_path):
                    with open(view_path, 'w', encoding='UTF-8'):
                        pass

    @staticmethod
    def parse_urls(app_name, dir_path, view_list):
        with open(os.path.join(dir_path, 'urls.py'), 'r+', encoding='UTF-8') as f:
            lines = f.readlines()
            url_note = []
            url_import = []
            url_path = []
            status = ''
            if len(lines) == 0:
                url_import = ["from django.conf.urls import url\n",
                              "\n"]
                url_path = ["urlpatterns = [\n",
                            "\n",
                            "]\n"]
                """
                    from django.conf.urls import url\n

                    urlpatterns = [\n
                    \n
                    ]\n
                """
            for line in lines:

                if r'"""' in line:
                    if status == '':
                        status = 'note'
                    elif status == 'note':
                        status = ''
                        url_note.append(line)

                if status == 'note':
                    url_note.append(line)

                if status == 'path':
                    if ']\n' == line.replace(' ', ''):
                        status = 'end'
                    url_path.append(line)

                if status == 'end':
                    break

                if status == '':
                    if 'urlpatterns=[\n' == line.replace(' ', ''):
                        url_path.append(line)
                        status = 'path'
                    elif 'import' in line:
                        url_import.append(line)

            # 生成import字符串
            has_import_app_view = False
            has_import_url = False
            for line in url_import:
                if line.replace(' ', '').replace('\n', '') == 'import' + app_name + '.views':
                    has_import_app_view = True
                if 'from django.conf.urls import url'.replace(' ', '') in line.replace(' ', ''):
                    has_import_url = True

            # 遍历生成需要添加的url字符串
            add_urls = ''
            for view in view_list:

                is_has = False
                view_name = view['view_name']
                view_args = view['args']
                if len(view_args) > 0:
                    view_path = view_name + '/' + '/'.join(['(?P<' + arg + '>.*)' for arg in view_args])
                else:
                    view_path = view_name

                for line in url_path:
                    if view_name in line:
                        is_has = True
                if not is_has:
                    add_urls += "\turl('%s/$', %s.views.%s),\n" % (view_path, app_name, view_name)

            # 清空文件重新写入

            f.truncate()
            f.seek(0)

            for note in url_note:
                f.write(note)

            if not has_import_url:
                f.write("from django.conf.urls import url\n")
            for import_ in url_import:
                f.write(import_)
            if not has_import_app_view:
                f.write('import %s.views\n' % app_name)

            for i in range(len(url_path)):

                if i == 1:
                    f.write(url_path[i])
                    if add_urls != '':
                        f.write(add_urls)
                else:
                    f.write(url_path[i])
