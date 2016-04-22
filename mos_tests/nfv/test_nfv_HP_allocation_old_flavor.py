#    Copyright 2016 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import logging
import pytest
from mos_tests.functions import network_checks
from mos_tests.nfv.base import TestBaseNFV

logger = logging.getLogger(__name__)

@pytest.mark.check_env_('is_vlan')
class TestHugePages(TestBaseNFV):

    @pytest.mark.check_env_('has_2_or_more_computes')
    @pytest.mark.undestructive
    @pytest.mark.parametrize(
        'nfv_flavor', [[[['m1.small.hpgs', 512, 1, 1],
                         [{'hw:mem_page_size': 2048}]],
                        [['m1.small.old', 512, 1, 1],
                         [{'hw:mem_page_size': 2048}, ]]]],
        indirect=['nfv_flavor'])
    @pytest.mark.testrail_id('838311')
    def test_VLAN_Allo_2M_HP_vms_req_HP_vms_with_old_flavor(self, env, os_conn, networks, nfv_flavor, keypair,
                                                            security_group, volume, aggregate):
        """
        This test checks that Huge pages set for vm1, vm2 and vm3 shouldn't use Huge pages, connectivity works properly
        Steps:
        1. Create net01, subnet.
        2. Create net 02, subnet.
        3. Create router, set gateway and add interfaces to both networks
        4. Launch vms using m1.small.hpgs flavor: vm1, vm3 on compute-1, vm2 on compute-2. For vm1 use new flavor,
        for vm2 and vm3 - old
        5. Locate the part of all instances configuration that is relevant to huge pages: #on controller
        hypervisor=nova show hpgs-test | grep OS-EXT-SRV-ATTR:host | cut -d\| -f3 instance=nova show hpgs-test |
        grep OS-EXT-SRV-ATTR:instance_name | cut -d\| -f3 # on compute virsh dumpxml $instance |awk '/memoryBacking/
        {p=1}; p; /\/numatune/ {p=0}'
        6. ping vm2 from vm1
        7. ping vm2 from vm3
        8. ping vm3 from vm1
        9. Check that it was allocated only HP for vm1
        """

        hosts = aggregate.hosts

        vm_0 = os_conn.create_server(
            name='vm1', flavor=nfv_flavor[0].id, key_name=keypair.name,
            nics=[{'net-id': networks[0]}],
            availability_zone='nova:{}'.format(hosts[0]),
            security_groups=[security_group.id])
        vm_1 = os_conn.create_server(
            name='vm2', flavor=nfv_flavor[0].id, key_name=keypair.name,
            availability_zone='nova:{}'.format(hosts[1]),
            security_groups=[security_group.id],
            nics=[{'net-id': networks[1]}])
        vm_2 = os_conn.create_server(
            name='vm3', flavor=nfv_flavor[0].id, key_name=keypair.name,
            nics=[{'net-id': networks[1]}],
            availability_zone='nova:{}'.format(hosts[1]),
            security_groups=[security_group.id])
        vms = [vm_0, vm_1, vm_2]

        self.check_pages(os_conn, hosts[0], total_pages=1024, free_pages=768)
        self.check_pages(os_conn, hosts[1], total_pages=1024, free_pages=512)
        for vm in vms:
            self.check_instance_page_size(os_conn, vm, size=2048)
        network_checks.check_vm_connectivity(env, os_conn)


