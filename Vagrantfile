# set up the default terminal
ENV["TERM"]="linux"

Vagrant.configure("2") do |config|

  # set the image for the vagrant box
  config.vm.box = "opensuse/Leap-15.3.x86_64"

  # st the static IP for the vagrant box
  config.vm.network "private_network", ip: "192.168.50.4"

  # portforwarding towards productcatalogservice for gRPC testing
  config.vm.network "forwarded_port", guest: 30550, host: 30550

  # consifure the parameters for VirtualBox provider
  config.vm.provider "virtualbox" do |vb|
    vb.memory = "8192"
    vb.cpus = 4
    vb.customize ["modifyvm", :id, "--ioapic", "on"]
  end
  config.vm.provision "shell", inline: <<-SHELL
    # install prerequisites
    sudo zypper refresh
    sudo zypper --non-interactive install bzip2
    sudo zypper --non-interactive install etcd
    sudo zypper --non-interactive install apparmor-parser
    # install a k3s cluster
    curl -sfL https://get.k3s.io | K3S_KUBECONFIG_MODE="644" sh -
    # install Helm
    curl https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 | bash
  SHELL
end
